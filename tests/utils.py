import os

from libcloud.storage.base import Container, StorageDriver
from libcloud.storage.drivers.dummy import DummyStorageDriver
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.drivers.minio import MinIOStorageDriver
from libcloud.storage.types import ContainerDoesNotExistError
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_test_engine() -> Engine:
    return create_engine(
        os.environ.get("ENGINE", "sqlite:///:memory:?check_same_thread=False")
    )


def get_or_create_container(driver: StorageDriver, name: str) -> Container:
    try:
        return driver.get_container(name)
    except ContainerDoesNotExistError:
        return driver.create_container(name)


def get_dummy_container(name: str) -> Container:
    return get_or_create_container(DummyStorageDriver("xxx", "xxx"), name)


def get_test_container(name: str) -> Container:
    provider = os.environ.get("STORAGE_PROVIDER", "LOCAL")
    if provider == "MINIO":
        key = os.environ.get("MINIO_KEY", "minioadmin")
        secret = os.environ.get("MINIO_SECRET", "minioadmin")
        host = os.environ.get("MINIO_HOST", "127.0.0.1")
        port = int(os.environ.get("MINIO_PORT", "9000"))
        secure = os.environ.get("MINIO_SECURE", "False").lower() == "true"
        return get_or_create_container(
            MinIOStorageDriver(
                key=key, secret=secret, host=host, port=port, secure=secure
            ),
            name,
        )
    else:  # noqa: RET505
        dir_path = os.environ.get("LOCAL_PATH", "/tmp/storage")
        os.makedirs(dir_path, 0o777, exist_ok=True)
        return get_or_create_container(LocalStorageDriver(dir_path), name)
