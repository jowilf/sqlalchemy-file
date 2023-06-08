import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy_file import File, FileField
from sqlalchemy_file.storage import StorageManager

Base = declarative_base()


# Define your model
class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)


# Configure Storage
os.makedirs("./upload_dir/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("./upload_dir").get_container("attachment")
StorageManager.add_storage("default", container)

# Save your model
engine = create_engine(
    "sqlite:///example.db", connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)

with Session(engine) as session:
    session.add(Attachment(name="attachment1", content=open("./example.txt", "rb")))
    session.add(Attachment(name="attachment2", content=b"Hello world"))
    session.add(Attachment(name="attachment3", content="Hello world"))
    file = File(content="Hello World", filename="hello.txt", content_type="text/plain")
    session.add(Attachment(name="attachment4", content=file))
    session.commit()
