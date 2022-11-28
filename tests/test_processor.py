import base64
import tempfile

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import ImageField

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


@pytest.fixture
def fake_image():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = base64.b64decode(
        "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"
    )
    file.write(data)
    file.seek(0)
    return file


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)
    cover = Column(
        ImageField(thumbnail_size=(128, 128))
    )  # will add thumbnail generator

    def __repr__(self):
        return "<Book: id %s ; name: %s; cover %s;>" % (
            self.id,
            self.title,
            self.cover,
        )  # pragma: no cover


class TestThumbnailGenerator:
    def setup_method(self, method) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-processor"))

    def test_create_image_with_thumbnail(self, fake_image) -> None:
        with Session(engine) as session:
            from PIL import Image

            session.add(Book(title="Pointless Meetings", cover=fake_image))
            session.flush()
            book = session.execute(
                select(Book).where(Book.title == "Pointless Meetings")
            ).scalar_one()
            assert book.cover["thumbnail"] is not None
            thumbnail = StorageManager.get_file(book.cover["thumbnail"]["path"])
            assert thumbnail is not None
            thumbnail = Image.open(thumbnail)
            assert max(thumbnail.width, thumbnail.height) == 128
            assert book.cover["thumbnail"]["width"] == thumbnail.width
            assert book.cover["thumbnail"]["height"] == thumbnail.height

    def teardown_method(self, method):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)
