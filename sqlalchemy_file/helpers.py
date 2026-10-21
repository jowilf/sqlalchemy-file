import json
import mimetypes
import os
import re
from builtins import RuntimeError
from tempfile import SpooledTemporaryFile
from typing import Any

INMEMORY_FILESIZE = 1024 * 1024
LOCAL_STORAGE_DRIVER_NAME = "Local Storage"


def get_metadata_file_obj(metadata: dict[str, Any]) -> "SpooledTemporaryFile[bytes]":
    f = SpooledTemporaryFile(INMEMORY_FILESIZE)  # noqa: SIM115
    f.write(json.dumps(metadata).encode())
    f.seek(0)
    return f


def get_content_from_file_obj(fileobj: Any) -> Any:
    """Provides a real file object from file content.

    Converts ``str`` and ``bytes`` to an actual file.
    """
    if isinstance(fileobj, (str, bytes)):
        f = SpooledTemporaryFile(INMEMORY_FILESIZE)  # noqa: SIM115
        f.write(fileobj.encode() if isinstance(fileobj, str) else fileobj)
        f.seek(0)
        return f
    if getattr(fileobj, "file", None) is not None:
        return fileobj.file
    return fileobj


def get_filename_from_fileob(fileobj: Any) -> Any:
    filename = getattr(fileobj, "filename", None)
    if filename:
        return filename
    name = getattr(fileobj, "name", None)
    # `name` can be a raw file descriptor (int).
    if isinstance(name, str):
        return os.path.basename(name)
    return "unnamed"


def get_content_type_from_fileobj(fileobj: Any, filename: str) -> Any:
    if getattr(fileobj, "content_type", None) is not None:
        return fileobj.content_type
    return mimetypes.guess_type(filename, strict=False)[0] or "application/octet-stream"


def get_content_size_from_fileobj(file: Any) -> Any:
    size = getattr(file, "size", None)
    if size is not None:
        return size
    if hasattr(file, "name"):
        try:
            return os.path.getsize(file.name)
        except (OSError, TypeError):
            pass
    if hasattr(file, "tell") and hasattr(file, "seek"):
        pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(pos)
        return size
    raise RuntimeError("Unable to determine the file's size.")  # pragma: no cover


def convert_size(size: str | int) -> int:
    """Convert a human readable size to a number of bytes: ``1k`` -> 1000, ``1Ki`` -> 1024."""
    if isinstance(size, str):
        m = re.fullmatch(r"^(\d+)\s*(k|([KM]i?))$", size)
        if m is None:
            raise ValueError(f"Invalid size {size}")
        value, si, _ = m.groups()
        si_map = {"k": 1000, "K": 1000, "M": 1000**2, "Ki": 1024, "Mi": 1024**2}
        return int(value) * si_map[si]
    return size


def flatmap(lists: list[list[Any]]) -> list[Any]:
    """Flattens a list of lists into a single list."""
    return [value for _list in lists for value in _list]
