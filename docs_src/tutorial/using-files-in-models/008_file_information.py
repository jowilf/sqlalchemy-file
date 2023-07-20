import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String, create_engine, select
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

with Session(engine) as session, open("./example.txt", "rb") as local_file:
    session.add(Attachment(name="attachment1", content=local_file))
    session.add(Attachment(name="attachment2", content=b"Hello world"))
    session.add(Attachment(name="attachment3", content="Hello world"))
    file = File(content="Hello World", filename="hello.txt", content_type="text/plain")
    session.add(Attachment(name="attachment4", content=file))
    session.commit()

    attachment = session.execute(
        select(Attachment).where(Attachment.name == "attachment3")
    ).scalar_one()
    assert attachment.content.saved  # saved is True for saved file
    assert attachment.content.file.read() == b"Hello world"  # access file content
    assert (
        attachment.content["filename"] is not None
    )  # `unnamed` when no filename are provided
    assert attachment.content["file_id"] is not None  # uuid v4
    assert attachment.content["upload_storage"] == "default"
    assert attachment.content["content_type"] is not None
    assert attachment.content["uploaded_at"] is not None
