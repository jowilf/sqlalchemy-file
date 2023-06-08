#Setup your storage

[StorageManager][sqlalchemy_file.storage.StorageManager] is the class which takes care of managing the whole Storage environment for the application.

## Terminology

**`Container:`** represents a container which can contain multiple objects. You can think of it as a folder on a file
system. Difference between container and a folder on file system is that containers cannot be nested. Some APIs and
providers (e.g. AWS) refer to it as a Bucket.

**`Object:`**  represents an object or so-called BLOB. (**SQLAlchemy-file** will store each file as an object)

For more information,
follow [Apache Libcloud Documentation](https://libcloud.readthedocs.io/en/stable/storage/index.html)

## Add Storage

Before adding a storage, the first thing you need is to setup an apache libcloud storage container.

=== "Local"

    ```Python
    import os
    from libcloud.storage.drivers.local import LocalStorageDriver
    from sqlalchemy_file.storage import StorageManager

    os.makedirs("./upload_dir/attachment", 0o777, exist_ok=True) # Make sure the directory exist
    my_container = LocalStorageDriver("./upload_dir").get_container("attachment")
    StorageManager.add_storage("default", container)

    ```
=== "MinIO"

    ```Python
    from libcloud.storage.types import Provider
    from libcloud.storage.types import ContainerAlreadyExistsError
    from libcloud.storage.providers import get_driver

    cls = get_driver(Provider.MINIO)
    driver = cls("api key", "api secret key", secure=False, host="127.0.0.1", port=9000)

    try:
        driver.create_container(container_name="attachment")
    except ContainerAlreadyExistsError:
        pass

    my_container = driver.get_container(container_name="attachment")

    ```
=== "S3"

    ```Python
    from libcloud.storage.providers import get_driver
    from libcloud.storage.types import Provider

    cls = get_driver(Provider.S3)
    driver = cls("api key", "api secret key")

    my_container = driver.get_container(container_name="attachment")

    ```
For more examples, see [Apache Libcloud Storage Examples](https://libcloud.readthedocs.io/en/stable/storage/examples.html)

Then, you can easily add your container to the storage manager

!!! example

    ```Python

    from sqlalchemy_file.storage import StorageManager

    StorageManager.add_storage("default", my_container)
    ```

## Using Multiple Storages

Multiple storage can be used inside the same application, most common operations require the full file path, so you can
use multiple storage without risk of collisions.

```Python
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

```

## Switching Default Storage

Once you started uploading files to a storage, it is best to avoid configuring another storage to the same name. Doing
that will probably break all the previously uploaded files and will cause confusion.

If you want to switch to a different storage for saving your files just configure two storage giving the new storage an
unique name and switch the default storage using the `StorageManager.set_default()` function.

```Python
from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager

first_container = LocalStorageDriver("./storage").get_container("first")
second_container = LocalStorageDriver("./storage").get_container("second")

StorageManager.add_storage("first", first_container)
StorageManager.add_storage("second", second_container)

assert StorageManager.get_default() == "first"

StorageManager.set_default("second")

assert StorageManager.get_default() == "second"

```
