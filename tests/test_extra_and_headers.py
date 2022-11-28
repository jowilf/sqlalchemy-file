import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file import File
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

from tests import DummyFile
from tests.utils import get_dummy_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()

EXTRA = {
    "acl": "private",
    "dummy_key": "dummy_value",
    "meta_data": {"key1": "value1", "key2": "value2"},
}

HEADERS = {"Access-Control-Allow-Origin": "http://test.com", "X-KEY": "xxxxxxx"}


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField())
    content_with_extra = Column(FileField(extra=EXTRA, headers=HEADERS))


@pytest.fixture
def engine() -> Engine:
    engine = get_test_engine()
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("test", get_dummy_container("test-extra-and-headers"))
    yield engine
    StorageManager._clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


def test_each_file_inherit_extra_from_field(session: Session):
    attachment = Attachment(name="Protected document", content_with_extra=DummyFile())
    session.add(attachment)
    session.commit()
    session.refresh(attachment)
    assert attachment.content_with_extra.file.object.extra["acl"] == "private"
    assert attachment.content_with_extra.file.object.extra["dummy_key"] == "dummy_value"
    assert (
        attachment.content_with_extra.file.object.extra["meta_data"]["key1"] == "value1"
    )
    assert (
        attachment.content_with_extra.file.object.extra["meta_data"]["key2"] == "value2"
    )


def test_overriding_default_extra(session: Session):
    attachment = Attachment(
        name="Public document",
        content_with_extra=File(DummyFile(), extra={"acl": "public-read"}),
    )
    session.add(attachment)
    session.commit()
    session.refresh(attachment)
    assert attachment.content_with_extra.file.object.extra["acl"] == "public-read"
