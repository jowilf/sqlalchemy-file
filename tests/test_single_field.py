import tempfile

import pytest
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy import Column, ForeignKey, Integer, String, select
from sqlalchemy.orm import Session, declarative_base, relationship
from sqlalchemy_file.file import File
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
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(fake_content.encode())
    file.seek(0)
    return file


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)

    article_id = Column(Integer, ForeignKey("article.id"))

    def __repr__(self):
        return f"<Attachment: id {self.id} ; name: {self.name}; content {self.content}; article_id {self.article_id}>"  # pragma: no cover


class Article(Base):
    __tablename__ = "article"

    id = Column(Integer, autoincrement=True, primary_key=True)
    title = Column(String(100), unique=True)

    attachments = relationship(Attachment, cascade="all, delete-orphan")

    def __repr__(self):
        return "<Article id: %s; name: %s; attachments: (%d) %s>" % (
            self.id,
            self.title,
            len(self.attachments),
            self.attachments,
        )  # pragma: no cover


class TestSingleField:
    def setup_method(self, method) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-simple-field"))

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

    def test_create_frompath(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(
                Attachment(
                    name="Create Fake file", content=File(content_path=fake_file.name)
                )
            )
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

    def test_edit_existing_none(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Testing None edit", content=None))
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Testing None edit")
            ).scalar_one()
            attachment.content = fake_file
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert attachment.content.file.read() == fake_content.encode()

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

    def test_edit_existing_multiple_flush(self, fake_file) -> None:
        with Session(engine) as session:
            attachment = Attachment(
                name="Multiple flush edit", content=b"first content"
            )
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            before_first_edit_fileid = attachment.content.file_id
            attachment.content = b"first edit"
            session.add(attachment)
            session.flush()
            session.refresh(attachment)
            first_edit_fileid = attachment.content.file_id
            attachment.content = b"second edit"
            session.add(attachment)
            session.flush()
            second_edit_fileid = attachment.content.file_id
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(before_first_edit_fileid)
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get().get_object(first_edit_fileid)
            assert StorageManager.get().get_object(second_edit_fileid) is not None
            assert attachment.content.file.read() == b"second edit"

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

    def test_relationship(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            article = Article(title="Great article!")
            session.add(article)
            article.attachments.append(Attachment(name="Banner", content=fake_file))
            session.commit()
            article = session.execute(
                select(Article).where(Article.title == "Great article!")
            ).scalar_one()
            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            article.attachments.remove(attachment)
            session.add(article)
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get_file(file_path)

    def test_relationship_rollback(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            article = Article(title="Awesome article about shark!")
            session.add(article)
            article.attachments.append(Attachment(name="Shark", content=fake_file))
            session.flush()
            article = session.execute(
                select(Article).where(Article.title == "Awesome article about shark!")
            ).scalar_one()
            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            session.rollback()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get_file(file_path)

    def test_relationship_cascade_delete(self, fake_file, fake_content) -> None:
        with Session(engine) as session:
            article = Article(title="Another Great article!")
            session.add(article)
            article.attachments.append(
                Attachment(name="Another Banner", content=fake_file)
            )
            session.commit()
            article = session.execute(
                select(Article).where(Article.title == "Another Great article!")
            ).scalar_one()
            attachment = article.attachments[0]
            assert attachment.content.file.read() == fake_content.encode()
            file_path = attachment.content.path
            session.delete(article)
            session.commit()
            with pytest.raises(ObjectDoesNotExistError):
                StorageManager.get_file(file_path)

    def test_relationship_cascade_delete_rollback(
        self, fake_file, fake_content
    ) -> None:
        with Session(engine) as session:
            article = Article(title="Another Great article for rollback!")
            session.add(article)
            article.attachments.append(
                Attachment(name="Another Banner for rollback", content=fake_file)
            )
            session.commit()
            article = session.execute(
                select(Article).where(
                    Article.title == "Another Great article for rollback!"
                )
            ).scalar_one()
            file_path = article.attachments[0].content.path
            assert StorageManager.get_file(file_path) is not None
            session.delete(article)
            session.flush()
            session.rollback()
            assert StorageManager.get_file(file_path) is not None

    def teardown_method(self, method):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)
