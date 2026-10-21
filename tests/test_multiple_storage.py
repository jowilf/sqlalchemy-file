import pytest
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

Base = declarative_base()


@pytest.fixture(autouse=True)
def sqla_storage(engine, sqla_storage_factory):
    """Set up the database schema and storage backend around each test."""
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("first", sqla_storage_factory("first"))
    StorageManager.add_storage("second", sqla_storage_factory("second"))
    yield
    StorageManager.get("first").delete()
    StorageManager.get("second").delete()
    Base.metadata.drop_all(engine)


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content_first = Column(FileField(upload_storage="first"))
    content_second = Column(FileField(upload_storage="second"))


class TestMultipleStorage:
    def test_multiple_storage(self, engine) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple Storage",
                    content_first=b"first",
                    content_second=b"second",
                )
            )
            session.flush()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Multiple Storage")
            ).scalar_one()
            first_fileid = attachment.content_first.file_id
            second_fileid = attachment.content_second.file_id
            assert StorageManager.get("first").get_object(first_fileid) is not None
            assert StorageManager.get("second").get_object(second_fileid) is not None
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get("first").get_object(second_fileid)
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get("second").get_object(first_fileid)
            session.rollback()
