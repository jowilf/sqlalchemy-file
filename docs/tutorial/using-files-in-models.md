# Using files in models

Attaching files to models is as simple as declaring a field on the model itself.

## Fields
You can use two Column type in your model.

### FileField

[FileField][sqlalchemy_file.types.FileField] is the main field, that can be used in your model to accept any files.

!!! example
    ```Python
    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_file import FileField

    Base = declarative_base()

    class Attachment(Base):
        __tablename__ = "attachment"

        id = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(String(50), unique=True)
        content = Column(FileField)
    ```
### ImageField

Inherits all attributes and methods from [FileField][sqlalchemy_file.types.FileField], but also validates that the
uploaded file is a valid image.
!!! note
    Using [ImageField][sqlalchemy_file.types.ImageField] is like
    using  [FileField][sqlalchemy_file.types.FileField]
    with [ImageValidator][sqlalchemy_file.validators.ImageValidator] and
    [ThumbnailGenerator][sqlalchemy_file.processors.ThumbnailGenerator]


!!! example
    ```Python
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy_file import ImageField

    Base = declarative_base()


    class Book(Base):
        __tablename__ = "book"

        id = Column(Integer, autoincrement=True, primary_key=True)
        title = Column(String(100), unique=True)
        cover = Column(ImageField(thumbnail_size=(128, 128)))
    ```
## Upload File

Let's say you defined your model like this
```python
class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(FileField)
```
and configure your storage like this
```python
container = LocalStorageDriver("./upload_dir").get_container("attachment")
StorageManager.add_storage("default", container)
```

### Save file object

Whenever a supported object is assigned to a [FileField][sqlalchemy_file.types.FileField] or [ImageField][sqlalchemy_file.types.ImageField]
it will be converted to a [File][sqlalchemy_file.file.File] object.
```python
with Session(engine) as session:
    session.add(Attachment(name="attachment1", content=open("./example.txt", "rb")))
    session.add(Attachment(name="attachment2", content=b"Hello world"))
    session.add(Attachment(name="attachment3", content="Hello world"))
    file = File(content="Hello World", filename="hello.txt", content_type="text/plain")
    session.add(Attachment(name="attachment4", content=file))
    session.commit()
```
The file itself will be uploaded to your configured storage, and only the [File][sqlalchemy_file.file.File]
information will be stored on the database as JSON.

### Retrieve file object

This is the same [File][sqlalchemy_file.file.File] object you will get back when reloading the models from database and the file itself is accessible
through the `.file` property.

!!! note
    Check the [File][sqlalchemy_file.file.File] documentation for all default attributes save into the database.

```python
with Session(engine) as session:
    attachment = session.execute(
            select(Attachment).where(Attachment.name == "attachment3")
        ).scalar_one()
    assert attachment.content.saved # saved is True for saved file
    assert attachment.content.file.read() == b"Hello world" # access file content
    assert attachment.content["filename"] is not None # `unnamed` when no filename are provided
    assert attachment.content["file_id"] is not None # uuid v4
    assert attachment.content["upload_storage"] == "default"
    assert attachment.content["content_type"] is not None
    assert attachment.content["uploaded_at"] is not None
```

### Save additional information

It's important to note that [File][sqlalchemy_file.file.File] object inherit from python `dict`.
Therefore, you can add additional information to your file object like a dict object. Just make sure to not use
the default attributes used by [File][sqlalchemy_file.file.File] object internally.

!!! Example
    ```python
    content = File(open("./example.txt", "rb"),custom_key1="custom_value1", custom_key2="custom_value2")
    content["custom_key3"] = "custom_value3"
    attachment = Attachment(name="Dummy", content=content)

    session.add(attachment)
    session.commit()
    session.refresh(attachment)

    assert attachment.custom_key1 == "custom_value1"
    assert attachment.custom_key2 == "custom_value2"
    assert attachment["custom_key3"] == "custom_value3"
    ```

!!! important
    [File][sqlalchemy_file.file.File] provides also attribute style access.
    You can access your keys as attributes.

### Extra & Headers

`Apache-libcloud` allow you to store each object with some `extra` attributes or additional `headers`.

They are two ways to add `extra` and `headers` with *sqlalchemy-file*

- on field declaration (shared by all associated files)

```python

class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    content = Column(
        FileField(
            extra={
                "acl": "private",
                "dummy_key": "dummy_value",
                "meta_data": {"key1": "value1", "key2": "value2"},
            },
            headers={
                "Access-Control-Allow-Origin": "http://test.com",
                "Custom-Key": "xxxxxxx",
            },
        )
    )

```

- in your [File][sqlalchemy_file.file.File] object

!!! important
    When the Field has default `extra` attribute, it's overridden by [File][sqlalchemy_file.file.File] object `extra`
    attribute
```python hl_lines="4"
with Session(engine) as session:
    attachment = Attachment(
            name="Public document",
            content=File(DummyFile(), extra={"acl": "public-read"}),
        )
    session.add(attachment)
    session.commit()
    session.refresh(attachment)

    assert attachment.content.file.object.extra["acl"] == "public-read"
```
### Metadata

!!! warning
    This attribute is now deprecated, migrate to [extra](#extra-headers)

*SQLAlchemy-file* store the uploaded file with some metadata. Only `filename` and `content_type` are sent by default,
. You can complete with `metadata` key inside your [File][sqlalchemy_file.file.File] object.

!!! Example
    ```py hl_lines="2"
    with Session(engine) as session:
        content = File(DummyFile(), metadata={"key1": "val1", "key2": "val2"})
        attachment = Attachment(name="Additional metadata", content=content)
        session.add(attachment)
        session.commit()
        attachment = session.execute(
            select(Attachment).where(Attachment.name == "Additional metadata")
        ).scalar_one()
        assert attachment.content.file.object.meta_data["key1"] == "val1"
        assert attachment.content.file.object.meta_data["key2"] == "val2"
    ```

## Uploading on a Specific Storage

By default, all the files are uploaded on the default storage which is the first added storage. This can be changed
by passing a `upload_storage` argument explicitly on field declaration:

```Python
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

```

## Validators

File validators get executed just before saving the uploaded file.

They can raise [ValidationError][sqlalchemy_file.exceptions.ValidationError] when
the uploaded files are not compliant with the validator conditions.

Multiple validators can be chained together to validate one file.

Validators can add additional properties to the file object. For example
[ImageValidator][sqlalchemy_file.validators.ImageValidator] add `width` and `height` to
the file object.

**SQLAlchemy-file** has built-in validators to get started, but you can create your own validator
by extending [Validator][sqlalchemy_file.validators.Validator] base class.

Built-in validators:

1. [SizeValidator][sqlalchemy_file.validators.SizeValidator] : Validate file maximum size
2. [ContentTypeValidator][sqlalchemy_file.validators.ContentTypeValidator]: Validate file mimetype
3. [ImageValidator][sqlalchemy_file.validators.ImageValidator]: Validate image

!!! example
    ```Python
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base

    from sqlalchemy_file import FileField
    from sqlalchemy_file.validators import ContentTypeValidator, SizeValidator

    Base = declarative_base()


    class Attachment(Base):
        __tablename__ = "attachment"

        id = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(String(50), unique=True)
        content = Column(
            FileField(
                validators=[
                    SizeValidator("500k"),
                    ContentTypeValidator(["text/plain", "text/csv"]),
                ]
            )
        )
    ```

## Processors
File processors get executed just after saving the uploaded file. They can be use
to generate additional files and attach it to the column. For example, [ThumbnailGenerator][sqlalchemy_file.processors.ThumbnailGenerator]
generate thumbnail from original image.

Multiple processors can be chained together. They will be executed in order.


Processors can add additional properties to the file object. For example
[ThumbnailGenerator][sqlalchemy_file.processors.ThumbnailGenerator] add generated
`thumbnail` file information into the file object.

!!! example
    ```Python
    from sqlalchemy import Column, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy_file import ImageField
    from sqlalchemy_file.processors import ThumbnailGenerator

    Base = declarative_base()


    class Book(Base):
        __tablename__ = "book"

        id = Column(Integer, autoincrement=True, primary_key=True)
        title = Column(String(100), unique=True)
        cover = Column(ImageField(processors=[ThumbnailGenerator()]))
    ```

## Multiple Files

The best way to handle multiple files, is to use SQLAlchemy relationships

!!! example
    ```Python
    from sqlalchemy import Column, ForeignKey, Integer, String
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    from sqlalchemy_file import FileField

    Base = declarative_base()


    class Attachment(Base):
        __tablename__ = "attachment"

        id = Column(Integer, autoincrement=True, primary_key=True)
        name = Column(String(50), unique=True)
        content = Column(FileField)

        article_id = Column(Integer, ForeignKey("article.id"))


    class Article(Base):
        __tablename__ = "article"

        id = Column(Integer, autoincrement=True, primary_key=True)
        title = Column(String(100), unique=True)

        attachments = relationship(Attachment, cascade="all, delete-orphan")
    ```

However, if you want to save multiple files directly in your model, set
`multiple=True` on field declaration:

```Python hl_lines="18 36-45"
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy_file import File, FileField
from sqlalchemy_file.storage import StorageManager

Base = declarative_base()


class Attachment(Base):
    __tablename__ = "attachment"

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(50), unique=True)
    multiple_content = Column(FileField(multiple=True))


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
    session.add(
        Attachment(
            name="attachment1",
            multiple_content=[
                "from str",
                b"from bytes",
                open("./example.txt", "rb"),
                File(
                    content="Hello World",
                    filename="hello.txt",
                    content_type="text/plain",
                ),
            ],
        )
    )
    session.commit()
```

Validators and processors will be applied to each file, and the return models
is a list of [File][sqlalchemy_file.file.File] object.

## Session Awareness

Whenever an object is deleted or a rollback is performed the files uploaded during the unit of work or attached to
the deleted objects are automatically deleted.
