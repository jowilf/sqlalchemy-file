from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.types import FileField

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content_first = Column(FileField(upload_storage="first"))
    content_second = Column(FileField(upload_storage="second"))


first_container = LocalStorageDriver("./storage").get_container("first")
second_container = LocalStorageDriver("./storage").get_container("second")

StorageManager.add_storage("first", first_container)
StorageManager.add_storage("second", second_container)
