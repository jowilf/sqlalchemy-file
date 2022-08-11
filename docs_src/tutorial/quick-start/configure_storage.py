import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager

# Configure Storage
os.makedirs("/tmp/storage/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("/tmp/storage").get_container("attachment")
StorageManager.add_storage("default", container)
