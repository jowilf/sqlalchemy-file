import tempfile

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy_file.exceptions import SizeValidationError
from sqlalchemy_file.helpers import convert_size
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField
from sqlalchemy_file.validators import SizeValidator

from tests.utils import get_test_container, get_test_engine

engine = get_test_engine()
Base = declarative_base()


@pytest.fixture
def fake_huge_file():
    file = tempfile.NamedTemporaryFile()
    file.write(b"\x00" * 6000)
    file.seek(0)
    return file


@pytest.fixture
def fake_valid_file():
    file = tempfile.NamedTemporaryFile()
    file.write(b"\x00" * 3000)
    file.seek(0)
    return file


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField(validators=[SizeValidator("5K")]))

    def __repr__(self):
        return f"<Attachment: id {self.id} ; name: {self.name}; content {self.content}>"  # pragma: no cover


class TestSizeValidator:
    def setup_method(self, method) -> None:
        Base.metadata.create_all(engine)
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-size-validator"))

    def test_size_converter(self) -> None:
        assert convert_size(100) == 100
        assert convert_size("3k") == 3 * 1000
        assert convert_size("4K") == 4 * 1000
        assert convert_size("2M") == 2 * 1000**2
        assert convert_size("3Ki") == 3 * 1024
        assert convert_size("3Mi") == 3 * 1024**2
        with pytest.raises(ValueError):
            convert_size("25")
        with pytest.raises(ValueError):
            convert_size("25V")

    def test_size_validator_large_file(self, fake_huge_file) -> None:
        with Session(engine) as session:
            session.add(Attachment(name="Huge File", content=fake_huge_file))
            with pytest.raises(SizeValidationError):
                session.flush()

    def test_size_validator_valid_size(self, fake_valid_file) -> None:
        with Session(engine) as session:
            attachment = Attachment(name="Valid File Size", content=fake_valid_file)
            session.add(attachment)
            session.commit()
            session.refresh(attachment)
            assert StorageManager.get_file(attachment.content.path) is not None
            print(type(attachment.content.file))
            print(attachment.content.file)
            assert attachment.content.file is not None

    def teardown_method(self, method):
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(engine)
