# Quick Start

## Installation

You can simply install **SQLAlchemy-file** from the PyPi:

### PIP

```shell
$ pip install sqlalchemy-file
```

### Poetry

```shell
$ poetry add sqlalchemy-file
```

## Usage

Getting SQLAlchemy-file setup in your code is really easy:

* Add [FileField][sqlalchemy_file.types.FileField] Column to your SQLAlchemy Model

!!! info
    When `upload_storage` is not specified, [FileField][sqlalchemy_file.types.FileField] will use the default storage which is the first added storage

```Python hl_lines="14 4"
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_file import FileField

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)


engine = create_engine(
    "sqlite:///example.db", connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)

```

* Configure Storage

**SQLAlchemy-file** store files through Apache
Libcloud [Object Storage API](https://libcloud.readthedocs.io/en/stable/storage/index.html) .The `StorageManager` is the
entity in charge of configuring and handling file storages inside your application. To start uploading files, add at
least one storage.

This can be done by using [StorageManager.add_storage()][sqlalchemy_file.storage.StorageManager.add_storage] which accepts a storage name (used to identify the storage in
case of multiple storages)
and the Apache Libcloud container which will be use for this storage.

!!! note
    The first added storage will be used as default storage

```Python hl_lines="3  23-25"
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_file import FileField
from sqlalchemy_file.storage import StorageManager

Base = declarative_base()


# Define your model
class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)


# Configure Storage
os.makedirs("/tmp/storage/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("/tmp/storage").get_container("attachment")
StorageManager.add_storage("default", container)


```

* Save your model

You can attach ``str``, ``bytes`` or any python ``file`` object to the column

**SQLAlchemy-file** will try to guess filename and content-type from attached file but you can use
`sqlalchemy_file.File` object to provide custom filename and content-type

```Python hl_lines="36-38 40-41"
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from sqlalchemy_file import FileField, File
from sqlalchemy_file.storage import StorageManager

Base = declarative_base()


# Define your model
class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)


# Configure Storage
os.makedirs("/tmp/storage/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("/tmp/storage").get_container("attachment")
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
    # Use sqlalchemy_file.File object to provide custom filename and content_type
    file = File(content="Hello World", filename="hello.txt", content_type="text/plain")
    session.add(Attachment(name="attachment4", content=file))
    session.commit()
```
