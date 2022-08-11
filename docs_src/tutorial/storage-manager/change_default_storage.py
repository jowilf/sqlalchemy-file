from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy_file.storage import StorageManager

first_container = LocalStorageDriver("./storage").get_container("first")
second_container = LocalStorageDriver("./storage").get_container("second")

StorageManager.add_storage("first", first_container)
StorageManager.add_storage("second", second_container)

assert StorageManager.get_default() == "first"

StorageManager.set_default("second")

assert StorageManager.get_default() == "second"
