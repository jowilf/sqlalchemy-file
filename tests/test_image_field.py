import base64
import tempfile

import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.exceptions import ContentTypeValidationError, InvalidImageError
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import ImageField

Base = declarative_base()


@pytest.fixture(autouse=True)
def sqla_storage(engine, sqla_storage_factory):
    """Set up the database schema and storage backend around each test."""
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("test", sqla_storage_factory("test-image-field"))
    yield
    for obj in StorageManager.get().list_objects():
        obj.delete()
    StorageManager.get().delete()
    Base.metadata.drop_all(engine)


@pytest.fixture
def fake_text_file():
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(b"Trying to save text file as image")
    file.seek(0)
    return file


@pytest.fixture
def fake_invalid_image():
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(b"Pass through content type validation")
    file.seek(0)
    return file


@pytest.fixture
def fake_valid_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_valid_image(fake_valid_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    data = fake_valid_image_content
    file.write(data)
    file.seek(0)
    return file


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)
    cover = Column(ImageField)

    def __repr__(self):
        return f"<Book: id {self.id} ; name: {self.title}; cover {self.cover};>"  # pragma: no cover


class TestImageField:
    def test_autovalidate_content_type(self, engine, fake_text_file) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_text_file))
            with pytest.raises(ContentTypeValidationError):
                session.flush()

    def test_autovalidate_image(self, engine, fake_invalid_image) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_invalid_image))
            with pytest.raises(InvalidImageError):
                session.flush()

    def test_create_image(
        self, engine, fake_valid_image, fake_valid_image_content
    ) -> None:
        with Session(engine) as session:
            session.add(Book(title="Pointless Meetings", cover=fake_valid_image))
            session.flush()
            book = session.execute(
                select(Book).where(Book.title == "Pointless Meetings")
            ).scalar_one()
            assert book.cover.file.read() == fake_valid_image_content
            assert book.cover["width"] is not None
            assert book.cover["height"] is not None
