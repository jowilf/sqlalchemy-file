from libcloud.storage.base import Container, StorageDriver
from libcloud.storage.drivers.dummy import DummyStorageDriver
from libcloud.storage.types import ContainerDoesNotExistError


def get_or_create_container(driver: StorageDriver, name: str) -> Container:
    try:
        return driver.get_container(name)
    except ContainerDoesNotExistError:
        return driver.create_container(name)


def get_dummy_container(name: str) -> Container:
    return get_or_create_container(DummyStorageDriver("xxx", "xxx"), name)
