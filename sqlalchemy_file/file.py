import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy_file.base import BaseFile
from sqlalchemy_file.helpers import (
    get_content_from_file_obj,
    get_content_size_from_fileobj,
    get_content_type_from_fileobj,
    get_filename_from_fileob,
)
from sqlalchemy_file.processors import Processor
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.stored_file import StoredFile
from sqlalchemy_file.validators import Validator


class File(BaseFile):
    """
    Takes a file as content and uploads it to the appropriate storage
    according to the attached Column and file information into the
    database as JSON.

    Default attributes provided for all ``File`` include:

    Attributes:

        filename (str):  This is the name of the uploaded file
        file_id:   This is the generated UUID for the uploaded file
        path:            This is a  compination of `upload_storage` and `file_id` separated by
                        `/`. This will be use later to retrieve the file
        content_type:   This is the content type of the uploaded file
        uploaded_at (datetime):    This is the upload date in ISO format
        url (str):            CDN url of the uploaded file
        file:           Only available for saved content, internally call
                      [StorageManager.get_file()][sqlalchemy_file.storage.StorageManager.get_file]
                      on path and return an instance of `StoredFile`
    """

    def __init__(
        self,
        content: Any,
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> None:
        super().__init__()
        if isinstance(content, dict):
            object.__setattr__(self, "original_content", None)
            object.__setattr__(self, "saved", True)
            self.update(content)
            self._freeze()
        else:
            self.original_content = get_content_from_file_obj(content)
            filename = filename or get_filename_from_fileob(content)
            content_type = content_type or get_content_type_from_fileobj(
                content, filename
            )
            self.update(
                {
                    "filename": filename,
                    "content_type": content_type,
                    "size": get_content_size_from_fileobj(self.original_content),
                    "files": [],
                }
            )
            self._thaw()

    def apply_validators(self, validators: List[Validator], key: str = "") -> None:
        """Apply validators to current file"""
        for validator in validators:
            validator.process(self, key)

    def apply_processors(
        self,
        processors: List[Processor],
        upload_storage: Optional[str] = None,
    ) -> None:
        """Apply processors to current file"""
        for processor in processors:
            processor.process(self, upload_storage)
        self._freeze()

    def save_to_storage(self, upload_storage: Optional[str] = None) -> None:
        """Save current file into provided `upload_storage`"""
        stored_file = self.store_content(
            self.original_content,
            upload_storage,
            metadata={"filename": self.filename, "content_type": self.content_type},
        )
        self["file_id"] = stored_file.name
        self["uploaded_at"] = datetime.utcnow().isoformat()
        self["path"] = "%s/%s" % (upload_storage, stored_file.name)
        self["url"] = stored_file.get_cdn_url()
        self["saved"] = True

    def store_content(
        self,
        content: Any,
        upload_storage: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredFile:
        """Store content into provided `upload_storage`
        with additional `metadata`. Can be use by processors
        to store additional files.
        """
        name = name or str(uuid.uuid4())
        stored_file = StorageManager.save_file(name, content, upload_storage, metadata)
        self["files"].append("%s/%s" % (upload_storage, name))
        return stored_file

    def encode(self) -> Dict[str, Any]:
        return {k: v for k, v in self.items() if k not in ["original_content"]}

    @classmethod
    def decode(cls, data: Any) -> "File":
        return cls(data)

    @property
    def file(self) -> "StoredFile":
        if self.get("saved", False):
            return StorageManager.get_file(self["path"])
        raise RuntimeError("Only available for saved file")
