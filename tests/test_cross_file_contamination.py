"""Regression tests for cross-file contamination of shared state.

``extra``/``headers`` can be configured once per column or shared between
``File`` objects: each file must get its own copy, so metadata never leaks
between files and the caller's dicts are never mutated. Likewise,
``ThumbnailGenerator`` must not overwrite the original file's ``meta_data``,
and ``FileField``/``ImageField`` must not append to caller-provided lists.
"""

import base64
import copy
import io
from typing import Any

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file import File
from sqlalchemy_file.processors import Processor
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField, ImageField
from sqlalchemy_file.validators import Validator

Base = declarative_base()


@pytest.fixture(autouse=True)
def sqla_storage(engine, sqla_storage_factory):
    """Set up the database schema and storage backend around each test."""
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage(
        "test", sqla_storage_factory("test-cross-file-contamination")
    )
    yield
    for obj in StorageManager.get().list_objects():
        obj.delete()
    StorageManager.get().delete()
    Base.metadata.drop_all(engine)


# Single dicts reused by every file of a column: how extras are used in practice.
COLUMN_EXTRA: dict[str, Any] = {"acl": "private", "meta_data": {"project": "contam"}}
MULTIPLE_EXTRA: dict[str, Any] = {"acl": "public-read"}


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField(extra=COLUMN_EXTRA))

    def __repr__(self):  # pragma: no cover
        return f"<Attachment: id {self.id} ; name: {self.name}>"


class GalleryItem(Base):
    __tablename__ = "gallery_item"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    contents = Column(FileField(multiple=True, extra=MULTIPLE_EXTRA))

    def __repr__(self):  # pragma: no cover
        return f"<GalleryItem: id {self.id} ; name: {self.name}>"


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)
    cover = Column(ImageField(thumbnail_size=(128, 128)))

    def __repr__(self):  # pragma: no cover
        return f"<Book: id {self.id} ; title: {self.title}>"


@pytest.fixture
def fake_png_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


class TestCrossFileContamination:
    def test_save_to_storage_does_not_mutate_caller_extra(self) -> None:
        extra: dict[str, Any] = {"acl": "private"}
        file = File(b"Content", filename="simple-call.txt", extra=extra)
        file.save_to_storage("test")
        # The caller's dict stays untouched; the file gets its own copy.
        assert extra == {"acl": "private"}
        assert file["extra"] is not extra
        assert file["extra"]["acl"] == "private"
        assert file["extra"]["content_type"] == "text/plain"
        assert file["extra"]["meta_data"]["filename"] == "simple-call.txt"

    def test_column_extra_isolated_per_file(self, engine) -> None:
        snapshot = copy.deepcopy(COLUMN_EXTRA)
        with Session(engine) as session:
            first = Attachment(
                name="first", content=File(b"first content", filename="first.txt")
            )
            second = Attachment(
                name="second", content=File(b"second content", filename="second.txt")
            )
            session.add_all([first, second])
            session.flush()
            file_first, file_second = first.content, second.content
            # The shared dict stays pristine; each file owns its copy.
            assert snapshot == COLUMN_EXTRA
            assert "content_type" not in COLUMN_EXTRA
            assert file_first["extra"] is not COLUMN_EXTRA
            assert file_second["extra"] is not COLUMN_EXTRA
            assert file_first["extra"] is not file_second["extra"]
            assert file_first["extra"]["meta_data"]["filename"] == "first.txt"
            assert file_second["extra"]["meta_data"]["filename"] == "second.txt"
            session.commit()
            session.refresh(first)
            session.refresh(second)
            assert first.content["extra"]["meta_data"]["filename"] == "first.txt"
            assert second.content["extra"]["meta_data"]["filename"] == "second.txt"

    def test_multiple_field_extra_isolated_per_file(self, engine) -> None:
        snapshot = copy.deepcopy(MULTIPLE_EXTRA)
        with Session(engine) as session:
            item = GalleryItem(
                name="gallery",
                contents=[
                    File(
                        b"first content", filename="first.png", content_type="image/png"
                    ),
                    File(b"second content", filename="second.txt"),
                ],
            )
            session.add(item)
            session.flush()
            file_first, file_second = item.contents
            assert snapshot == MULTIPLE_EXTRA
            assert file_first["extra"] is not MULTIPLE_EXTRA
            assert file_first["extra"] is not file_second["extra"]
            assert file_first["extra"]["meta_data"]["filename"] == "first.png"
            assert file_first["extra"]["content_type"] == "image/png"
            assert file_second["extra"]["meta_data"]["filename"] == "second.txt"
            assert file_second["extra"]["content_type"] == "text/plain"
            session.commit()
            session.refresh(item)
            assert item.contents[0]["extra"]["meta_data"]["filename"] == "first.png"
            assert item.contents[0]["extra"]["content_type"] == "image/png"
            assert item.contents[1]["extra"]["meta_data"]["filename"] == "second.txt"
            assert item.contents[1]["extra"]["content_type"] == "text/plain"

    def test_shared_file_extra_between_files(self, engine) -> None:
        """Caller reuses the same dict for two files: neither must be affected
        by the other's save.
        """
        shared: dict[str, Any] = {"acl": "public-read"}
        file_one = File(b"first content", filename="first.txt", extra=shared)
        file_two = File(b"second content", filename="second.txt", extra=shared)
        with Session(engine) as session:
            session.add_all(
                [
                    Attachment(name="shared-one", content=file_one),
                    Attachment(name="shared-two", content=file_two),
                ]
            )
            session.flush()
            assert shared == {"acl": "public-read"}
            assert file_one["extra"] is not shared
            assert file_two["extra"] is not shared
            assert file_one["extra"] is not file_two["extra"]
            assert file_one["extra"]["meta_data"]["filename"] == "first.txt"
            assert file_two["extra"]["meta_data"]["filename"] == "second.txt"

    def test_thumbnail_does_not_contaminate_original_file(
        self, engine, fake_png_content
    ) -> None:
        with Session(engine) as session:
            book = Book(
                title="Contaminated cover test",
                cover=File(
                    io.BytesIO(fake_png_content),
                    filename="cover.png",
                    content_type="image/png",
                ),
            )
            session.add(book)
            session.flush()
            cover = book.cover
            # The original file keeps its metadata; the thumbnail gets its own.
            assert cover["extra"]["content_type"] == "image/png"
            assert cover["extra"]["meta_data"]["filename"] == "cover.png"
            assert "width" not in cover["extra"]["meta_data"]
            assert "height" not in cover["extra"]["meta_data"]
            thumbnail = StorageManager.get_file(cover["thumbnail"]["path"])
            assert thumbnail.filename.startswith("cover.png")  # pragma: no branch
            assert ".thumbnail" in thumbnail.filename

    def test_field_constructor_does_not_mutate_shared_lists(self) -> None:
        validators: list[Validator] = []
        processors: list[Processor] = []
        ImageField(
            validators=validators, processors=processors, thumbnail_size=(64, 64)
        )
        FileField(validators=validators, processors=processors)
        # Field constructors must not append to the caller's lists.
        assert validators == []
        assert processors == []
