import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager

# Configure Storage
os.makedirs("./upload_dir/attachment", 0o777, exist_ok=True)
container = LocalStorageDriver("./upload_dir").get_container("attachment")
StorageManager.add_storage("default", container)
