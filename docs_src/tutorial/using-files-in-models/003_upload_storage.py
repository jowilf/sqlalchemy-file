from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_file import FileField
from sqlalchemy_file.storage import StorageManager

Base = declarative_base()
# Amazon S3 Container
amazon_s3_container = get_driver(Provider.S3)(
    "api key", "api secret key"
).get_container("example")

# MinIO Container
min_io_container = get_driver(Provider.MINIO)(
    "api key", "api secret key"
).get_container("example")

# Configure Storage
StorageManager.add_storage("amazon_s3_storage", amazon_s3_container)
StorageManager.add_storage("min_io_storage", min_io_container)


class AttachmentS3(Base):
    __tablename__ = "attachment_s3"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField(upload_storage="amazon_s3_storage"))


class AttachmentMinIO(Base):
    __tablename__ = "attachment_min_io"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content_min_io = Column(FileField(upload_storage="min_io_storage"))
