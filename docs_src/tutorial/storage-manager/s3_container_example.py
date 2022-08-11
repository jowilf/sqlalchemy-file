from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from sqlalchemy_file.storage import StorageManager

cls = get_driver(Provider.S3)
driver = cls("api key", "api secret key")

my_container = driver.get_container(container_name="attachment")

StorageManager.add_storage("default", my_container)
