import contextlib

from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerAlreadyExistsError, Provider
from sqlalchemy_file.storage import StorageManager

from .config import config

cls = get_driver(Provider.AZURE_BLOBS)
driver = cls(
    key=config.storage.key,
    secret=config.storage.secret,
    host=config.storage.host,
    port=config.storage.port,
    secure=config.storage.secure,
)


def init_storage() -> None:
    with contextlib.suppress(ContainerAlreadyExistsError):
        driver.create_container(container_name="category")

    container = driver.get_container(container_name="category")

    StorageManager.add_storage("category", container)
