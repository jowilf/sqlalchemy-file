import pytest
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.file import File
from sqlalchemy_file.processors import Processor
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

from tests import DummyFile
from tests.utils import get_dummy_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


class DictLikeCheckerProcessor(Processor):
    def process(self, file: "File", upload_storage=None):
        file["dummy_attr"] = "Dummy data"
        file["del_attr"] = True
        del file["del_attr"]
        with pytest.raises(AttributeError):
            delattr(file, "del_attr")


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField(processors=[DictLikeCheckerProcessor()]))
    multiple_content = Column(
        FileField(multiple=True, processors=[DictLikeCheckerProcessor()])
    )

    def __repr__(self):
        return f"<Attachment: id {self.id} ; name: {self.name}; content {self.content}; multiple_content {self.multiple_content}>"  # pragma: no cover


class TestResultValue:
    def setup_method(self, method) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_dummy_container("test-result-value"))

    def test_single_column_is_dictlike(self) -> None:
        with Session(engine) as session:
            attachment = Attachment(name="Single content", content=DummyFile())
            session.add(attachment)
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Single content")
            ).scalar_one()
            assert attachment.content.dummy_attr == "Dummy data"
            assert "del_attr" not in attachment.content

    def test_file_custom_attributes(self) -> None:
        with Session(engine) as session:
            content = File(
                DummyFile(), custom_key1="custom_value1", custom_key2="custom_value2"
            )
            attachment = Attachment(name="Custom attributes", content=content)
            session.add(attachment)
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Custom attributes")
            ).scalar_one()
            assert attachment.content["custom_key1"] == "custom_value1"
            assert attachment.content["custom_key2"] == "custom_value2"
            assert attachment.content.custom_key1 == "custom_value1"
            assert attachment.content.custom_key2 == "custom_value2"

    def test_file_additional_metadata_deprecated(self) -> None:
        with pytest.warns(
            DeprecationWarning, match="metadata attribute is deprecated"
        ), Session(engine) as session:
            metadata = {"key1": "val1", "key2": "val2"}
            content = File(DummyFile(), metadata=metadata)
            attachment = Attachment(name="Additional metadata", content=content)
            session.add(attachment)
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Additional metadata")
            ).scalar_one()
            assert attachment.content.file.object.meta_data["key1"] == "val1"
            assert attachment.content.file.object.meta_data["key2"] == "val2"

    def test_multiple_column_is_list_of_dictlike(self) -> None:
        with Session(engine) as session:
            attachment = Attachment(
                name="Multiple content",
                multiple_content=[DummyFile(5, 10), DummyFile(10, 20)],
            )
            session.add(attachment)
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Multiple content")
            ).scalar_one()
            assert isinstance(attachment.multiple_content, list)
            for content in attachment.multiple_content:
                assert content.dummy_attr == "Dummy data"
                assert "del_attr" not in content

    def test_column_cannot_edit_after_save(self) -> None:
        with Session(engine) as session:
            attachment = Attachment(name="Single content", content=DummyFile())
            session.add(attachment)
            session.commit()
            attachment = session.execute(
                select(Attachment).where(Attachment.name == "Single content")
            ).scalar_one()
            with pytest.raises(TypeError):
                attachment.content["another_dummy_attr"] = "Another Dummy data"
            with pytest.raises(TypeError):
                del attachment.content["dummy_attr"]
            with pytest.raises(TypeError):
                delattr(attachment.content, "dummy_attr")

    def test_multiple_column_cannot_edit_after_save(self) -> None:
        with Session(engine) as session:
            attachment = Attachment(
                name="Multiple content Freeze",
                multiple_content=[DummyFile(5, 10), DummyFile(10, 20)],
            )
            session.add(attachment)
            session.commit()
            m_attachment = session.execute(
                select(Attachment).where(Attachment.name == "Multiple content Freeze")
            ).scalar_one()
            # Cannot edit individual list element
            for content in m_attachment.multiple_content:
                with pytest.raises(TypeError):
                    content["another_dummy_attr"] = "Another Dummy data"
                with pytest.raises(TypeError):
                    del content["dummy_attr"]
                with pytest.raises(TypeError):
                    delattr(content, "dummy_attr")

    def teardown_method(self, method):
        Base.metadata.drop_all(engine)
