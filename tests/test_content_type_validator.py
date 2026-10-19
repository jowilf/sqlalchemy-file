import tempfile

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.exceptions import ContentTypeValidationError
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField
from sqlalchemy_file.validators import ContentTypeValidator

Base = declarative_base()


@pytest.fixture(autouse=True)
def sqla_storage(engine, sqla_storage_factory):
    """Set up the database schema and storage backend around each test."""
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("test", sqla_storage_factory("content-type-validator"))
    yield
    for obj in StorageManager.get().list_objects():
        obj.delete()
    StorageManager.get().delete()
    Base.metadata.drop_all(engine)


@pytest.fixture
def fake_txt_file():
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(b"This is a fake text file")
    file.flush()
    return file


@pytest.fixture
def fake_csv_file():
    file = tempfile.NamedTemporaryFile(suffix=".csv")
    file.write(b"This is a fake csv file")
    file.flush()
    return file


@pytest.fixture
def fake_pdf_file():
    file = tempfile.NamedTemporaryFile(suffix=".pdf")
    file.write(b"This is a fake pdf file")
    file.flush()
    return file


@pytest.fixture
def fake_file():
    file = tempfile.NamedTemporaryFile()
    file.write(b"This is a fake with unknown content type")
    file.flush()
    return file


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(
        FileField(validators=[ContentTypeValidator(["text/plain", "text/csv"])])
    )

    def __repr__(self):
        return f"<Attachment: id {self.id} ; name: {self.name}; content {self.content}>"  # pragma: no cover


class TestContentTypeValidator:
    def test_content_type_validator(
        self, engine, fake_file, fake_pdf_file, fake_csv_file, fake_txt_file
    ):
        with Session(engine) as session:
            attachment = Attachment(name="unknown file", content=fake_file)
            session.add(attachment)
            with pytest.raises(ContentTypeValidationError):
                session.flush()

        with Session(engine) as session:
            attachment = Attachment(name="pdf file", content=fake_pdf_file)
            session.add(attachment)
            with pytest.raises(ContentTypeValidationError):
                session.flush()

        with Session(engine) as session:
            attachment = Attachment(name="text file", content=fake_txt_file)
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.content.file is not None

        with Session(engine) as session:
            attachment = Attachment(name="csv file", content=fake_csv_file)
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.content.file is not None
