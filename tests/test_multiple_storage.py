import pytest
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content_first = Column(FileField(upload_storage="first"))
    content_second = Column(FileField(upload_storage="second"))


class TestMultipleStorage:
    def setup(self) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("first", get_test_container("first"))
        StorageManager.add_storage("second", get_test_container("second"))

    def test_multiple_storage(self) -> None:
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

    def teardown(self):
        StorageManager.get("first").delete()
        StorageManager.get("second").delete()
        Base.metadata.drop_all(engine)
