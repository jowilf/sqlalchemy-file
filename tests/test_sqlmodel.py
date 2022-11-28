import tempfile
from typing import Any

import pytest
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy import Column, select
from sqlalchemy_file.file import File
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField
from sqlmodel import Field, Session, SQLModel

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()


@pytest.fixture
def fake_content():
    return "This is a fake file"


@pytest.fixture
def fake_file(fake_content):
    file = tempfile.NamedTemporaryFile()
    file.write(fake_content.encode())
    file.seek(0)
    return file


class Attachment(SQLModel, table=True):
    __tablename__ = "attachment"

    id: int = Field(None, primary_key=True)
    name: str = Field(..., sa_column_kwargs={"unique": True})
    content: Any = Field(sa_column=Column(FileField))


class TestSQLModel:
    def setup_method(self, method) -> None:
        SQLModel.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-sqlmodel"))

    def test_create_from_string(self, fake_content) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Create fake string", content=fake_content))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Create fake string")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    def test_create_from_bytes(self, fake_content) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(name="Create Fake bytes", content=fake_content.encode())
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Create Fake bytes")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    def test_create_fromfile(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Create Fake file", content=fake_file))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Create Fake file")
            ).scalar_one()
            assert attachment.content.saved
            assert attachment.content.file.read() == fake_content.encode()

    def test_file_is_created_when_flush(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            attachment = Attachment(name="Create Fake file 2", content=File(fake_file))
            session.add(attachment)
            with pytest.raises(RuntimeError):
                assert attachment.content.file is not None
            session.flush()
            assert attachment.content.file is not None

    def test_create_rollback(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Create rollback", content=fake_file))
            session.flush()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Create rollback")
            ).scalar_one()
            file_id = attachment.content.file_id
            assert StorageManager.get().get_object(file_id) is not None
            session.rollback()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(file_id)

    def test_edit_existing(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Editing test", content=fake_file))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Editing test")
            ).scalar_one()
            old_file_id = attachment.content.file_id
            attachment.content = b"New content"
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(old_file_id)
            assert attachment.content.file.read() == b"New content"

    def test_edit_existing_rollback(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(name="Editing test rollback", content=b"Initial content")
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Editing test rollback")
            ).scalar_one()
            old_file_id = attachment.content.file_id
            attachment.content = b"New content"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            new_file_id = attachment.content.file_id
            session.rollback()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(new_file_id)
            assert StorageManager.get().get_object(old_file_id) is not None
            assert attachment.content.file.read() == b"Initial content"

    def test_delete_existing(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Deleting test", content=fake_file))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Deleting test")
            ).scalar_one()
            file_id = attachment.content.file_id
            assert StorageManager.get().get_object(file_id) is not None
            session.delete(attachment)
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(file_id)

    def test_delete_existing_rollback(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Deleting rollback test", content=fake_file))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Deleting rollback test")
            ).scalar_one()
            file_id = attachment.content.file_id
            assert StorageManager.get().get_object(file_id) is not None
            session.delete(attachment)
            session.flush()
            session.rollback()
            assert StorageManager.get().get_object(file_id) is not None

    def teardown_method(self, method):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        SQLModel.metadata.drop_all(engine)
