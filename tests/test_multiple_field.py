import tempfile

import pytest
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


@pytest.fixture
def fake_content():
    return "This is a fake file"


@pytest.fixture
def fake_file(fake_content):
    file = tempfile.NamedTemporaryFile()
    file.write(fake_content.encode())
    file.seek(0)
    return file


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    multiple_content = Column(FileField(multiple=True))

    def __repr__(self):
        return f"<Attachment: id {self.id} ; name: {self.name}; multiple_content {self.multiple_content}>"  # pragma: no cover


class TestMultipleField:
    def setup_method(self, method) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-multiple-field"))

    def test_create_multiple_content(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Create multiple",
                    multiple_content=[
                        "from str",
                        b"from bytes",
                        fake_file,
                    ],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Create multiple")
            ).scalar_one()
            assert attachment.multiple_content[0].file.read().decode() == "from str"
            assert attachment.multiple_content[1].file.read() == b"from bytes"
            assert attachment.multiple_content[2].file.read() == fake_content.encode()

    def test_create_multiple_content_rollback(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Create multiple content rollback",
                    multiple_content=[
                        "from str",
                        b"from bytes",
                        fake_file,
                    ],
                )
            )
            session.flush()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Create multiple content rollback"
                )
            ).scalar_one()
            paths = [p["path"] for p in attachment.multiple_content]
            assert all(StorageManager.get_file(path) is not None for path in paths)
            session.rollback()
            for path in paths:
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get_file(path)

    def test_edit_existing_multiple_content(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content edit all",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Multiple content edit all")
            ).scalar_one()
            old_paths = [f["path"] for f in attachment.multiple_content]
            attachment.multiple_content = [b"Content 1 edit", b"Content 2 edit"]
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert attachment.multiple_content[0].file.read() == b"Content 1 edit"
            assert attachment.multiple_content[1].file.read() == b"Content 2 edit"
            for path in old_paths:
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get_file(path)

    def test_edit_existing_multiple_content_rollback(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content edit all rollback",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content edit all rollback"
                )
            ).scalar_one()
            old_paths = [f["path"] for f in attachment.multiple_content]
            attachment.multiple_content = [b"Content 1 edit", b"Content 2 edit"]
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.multiple_content[0].file.read() == b"Content 1 edit"
            assert attachment.multiple_content[1].file.read() == b"Content 2 edit"
            new_paths = [f["path"] for f in attachment.multiple_content]
            session.rollback()
            for path in new_paths:
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get_file(path)
            for path in old_paths:
                assert StorageManager.get_file(path) is not None

    def test_edit_existing_multiple_content_add_element(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content add element",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content add element"
                )
            ).scalar_one()
            assert len(attachment.multiple_content) == 2
            attachment.multiple_content.append(b"Content 3")
            attachment.multiple_content += [b"Content 4"]
            attachment.multiple_content.extend([b"Content 5"])
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 5
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 2"
            assert attachment.multiple_content[2].file.read() == b"Content 3"
            assert attachment.multiple_content[3].file.read() == b"Content 4"
            assert attachment.multiple_content[4].file.read() == b"Content 5"

    def test_edit_existing_multiple_content_add_element_rollback(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content add element rollback",
                    multiple_content=[b"Content 1", b"Content 2"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content add element rollback"
                )
            ).scalar_one()
            attachment.multiple_content += [b"Content 3", b"Content 4"]
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 4
            path3 = attachment.multiple_content[2].path
            path4 = attachment.multiple_content[3].path
            assert StorageManager.get_file(path3) is not None
            assert StorageManager.get_file(path4) is not None
            session.rollback()
            assert len(attachment.multiple_content) == 2
            for path in (path3, path4):
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get_file(path)

    def test_edit_existing_multiple_content_remove_element(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content remove element",
                    multiple_content=[
                        b"Content 1",
                        b"Content 2",
                        b"Content 3",
                        b"Content 4",
                        b"Content 5",
                    ],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content remove element"
                )
            ).scalar_one()
            first_removed = attachment.multiple_content.pop(1)
            second_removed = attachment.multiple_content[3]
            attachment.multiple_content.remove(second_removed)
            third_removed = attachment.multiple_content[2]
            del attachment.multiple_content[2]
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 2
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 3"
            for file in (first_removed, second_removed, third_removed):
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get_file(file.path)

    def test_edit_existing_multiple_content_remove_element_rollback(self) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content remove element rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content remove element rollback"
                )
            ).scalar_one()
            attachment.multiple_content.pop(0)
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert len(attachment.multiple_content) == 2
            assert attachment.multiple_content[0].file.read() == b"Content 2"
            assert attachment.multiple_content[1].file.read() == b"Content 3"
            session.rollback()
            assert len(attachment.multiple_content) == 3
            assert attachment.multiple_content[0].file.read() == b"Content 1"
            assert attachment.multiple_content[1].file.read() == b"Content 2"
            assert attachment.multiple_content[2].file.read() == b"Content 3"

    def test_edit_existing_multiple_content_replace_element(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content replace",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Multiple content replace")
            ).scalar_one()
            before_replaced_path = attachment.multiple_content[1].path
            attachment.multiple_content[1] = b"Content 2 replaced"
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert attachment.multiple_content[1].file.read() == b"Content 2 replaced"
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get_file(before_replaced_path)

    def test_edit_existing_multiple_content_replace_element_rollback(
        self, fake_file
    ) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Multiple content replace rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Multiple content replace rollback"
                )
            ).scalar_one()
            attachment.multiple_content[1] = b"Content 2 replaced"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            assert attachment.multiple_content[1].file.read() == b"Content 2 replaced"
            new_path = attachment.multiple_content[1].path
            session.rollback()
            assert attachment.multiple_content[1].file.read() == b"Content 2"
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get_file(new_path)

    def test_delete_existing_multiple_content(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Deleting multiple content",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Deleting multiple content")
            ).scalar_one()
            file_ids = [f.file_id for f in attachment.multiple_content]
            for file_id in file_ids:
                assert StorageManager.get().get_object(file_id) is not None
            session.delete(attachment)
            session.commit()
            for file_id in file_ids:
                with pytest.raises(ObjectDoesNotExistError):
                    StorageManager.get().get_object(file_id)

    def test_delete_existing_multiple_content_rollback(self, fake_file) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Deleting multiple content rollback",
                    multiple_content=[b"Content 1", b"Content 2", b"Content 3"],
                )
            )
            session.commit()
            attachment = session.execute(
                select(Attachment).where(
                    Attachment.name == "Deleting multiple content rollback"
                )
            ).scalar_one()
            file_ids = [f.file_id for f in attachment.multiple_content]
            for file_id in file_ids:
                assert StorageManager.get().get_object(file_id) is not None
            session.delete(attachment)
            session.flush()
            session.rollback()
            for file_id in file_ids:
                assert StorageManager.get().get_object(file_id) is not None

    def teardown_method(self, method):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)
