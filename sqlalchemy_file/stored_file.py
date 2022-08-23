import json
import tempfile
from typing import Optional

from libcloud.storage.base import Object
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy_file.helpers import LOCAL_STORAGE_DRIVER_NAME


class StoredFile:
    def __init__(self, obj: Object) -> None:
        if obj.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            """Retrieve metadata from associated metadata file"""
            try:
                metadata_obj = obj.container.get_object(f"{obj.name}.metadata.json")
                obj.meta_data = json.load(open(metadata_obj.get_cdn_url()))
            except ObjectDoesNotExistError:
                pass
        self.name = obj.name
        self.filename = obj.meta_data.get("filename", "unnamed")
        self.content_type = obj.extra.get(
            "content_type",
            obj.meta_data.get("content_type", "application/octet-stream"),
        )
        self.object = obj

    def get_cdn_url(self) -> Optional[str]:
        try:
            return self.object.get_cdn_url()
        except NotImplementedError:
            return None

    def read(self, n: int = -1) -> bytes:
        if self.object.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            return open(self.object.get_cdn_url(), "rb").read(n)
        _file = tempfile.NamedTemporaryFile()
        self.object.download(_file.name, overwrite_existing=True)
        return _file.read(n)
