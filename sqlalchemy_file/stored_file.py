import io
import json

from libcloud.storage.base import Object
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy_file.helpers import LOCAL_STORAGE_DRIVER_NAME


class StoredFile(io.IOBase):
    """Represents a file that has been stored in a database. This class provides
    a file-like interface for reading the file content.

    Attributes:
        name: The name of the file (Same as file_id).
        filename: The original name of the uploaded file.
        content_type: The content type of the uploaded file.
        object: The `Object` representing the file in the storage service.
    """

    def __init__(self, obj: Object) -> None:
        if obj.driver.name == LOCAL_STORAGE_DRIVER_NAME:
            # Read metadata from the `<name>.metadata.json` sidecar.
            try:
                metadata_obj = obj.container.get_object(f"{obj.name}.metadata.json")
                with open(metadata_obj.get_cdn_url()) as metadata_file:
                    obj.meta_data = json.load(metadata_file)
            except (ObjectDoesNotExistError, ValueError, OSError):
                # Missing or corrupt sidecar: fall back to defaults.
                pass
        self.name = obj.name
        self.filename = obj.meta_data.get("filename", "unnamed")
        self.content_type = obj.extra.get(
            "content_type",
            obj.meta_data.get("content_type", "application/octet-stream"),
        )
        self.object = obj

    def get_cdn_url(self) -> str | None:
        """Retrieves the CDN URL of the file if available."""
        try:
            return self.object.get_cdn_url()
        except NotImplementedError:
            return None

    def read(  # ty: ignore[invalid-mutable-override]
        self, n: int = -1, chunk_size: int | None = None
    ) -> bytes:
        """Reads the content of the file.

        Arguments:
            n: The number of bytes to read. If not specified or set to -1,
                it reads the entire content of the file. Defaults to -1.
            chunk_size: The size of the chunks to read at a time.
                If not specified, the default chunk size of the storage provider will be used.

        """
        # Consume every chunk, otherwise large files are truncated
        # to the first one.
        return b"".join(
            self.object.range_as_stream(
                0, end_bytes=n if n > 0 else None, chunk_size=chunk_size
            )
        )

    def close(self) -> None:
        pass  # No-op: content is read from storage on demand.

    def seekable(self) -> bool:
        return False  # Seeking is not supported.  # pragma: no cover

    def writable(self) -> bool:
        return False  # Writing is not supported.  # pragma: no cover

    def readable(self) -> bool:
        return True  # Reading is supported.  # pragma: no cover
