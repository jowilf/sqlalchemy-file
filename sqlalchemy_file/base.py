import typing
from typing import Any, Literal, overload, override

STR_ATTRS = Literal[
    "url",
    "filename",
    "content_type",
    "file_id",
    "upload_storage",
    "uploaded_at",
    "path",
    "url",
]
BOOL_ATTRS = Literal["saved"]
INT_ATTRS = Literal["size"]
DICT_ATTRS = Literal["meta_data"]
STR_LIST_ATTRS = Literal["files"]


class BaseFile(typing.Dict[str, Any]):
    """Base class for file object.

    It keeps information on a content related to a specific storage.
    It is a specialized dictionary that provides also attribute style access,
    the dictionary parent permits easy encoding/decoding to JSON.

    """

    @overload
    def __getitem__(self, key: STR_ATTRS) -> str:
        ...

    @overload
    def __getitem__(self, key: INT_ATTRS) -> int:
        ...

    @overload
    def __getitem__(self, key: DICT_ATTRS) -> dict[str, str]:
        ...

    @overload
    def __getitem__(self, key: STR_LIST_ATTRS) -> list[str]:
        ...

    @overload
    def __getitem__(self, key: BOOL_ATTRS) -> bool:
        ...

    @override
    def __getitem__(self, key: str) -> Any:
        return dict.__getitem__(self, key)

    @overload
    def __getattr__(self, name: STR_ATTRS) -> str:
        ...

    @overload
    def __getattr__(self, name: INT_ATTRS) -> int:
        ...

    @overload
    def __getattr__(self, name: DICT_ATTRS) -> dict[str, str]:
        ...

    @overload
    def __getattr__(self, name: STR_LIST_ATTRS) -> list[str]:
        ...

    @overload
    def __getattr__(self, name: BOOL_ATTRS) -> bool:
        ...

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    @override
    def __setitem__(self, key: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("Already saved files are immutable")
        return dict.__setitem__(self, key, value)

    __setattr__ = __setitem__

    @override
    def __delattr__(self, name: str) -> None:
        if getattr(self, "_frozen", False):
            raise TypeError("Already saved files are immutable")

        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

    @override
    def __delitem__(self, key: str) -> None:
        if object.__getattribute__(self, "_frozen"):
            raise TypeError("Already saved files are immutable")
        dict.__delitem__(self, key)

    def _freeze(self) -> None:
        object.__setattr__(self, "_frozen", True)

    def _thaw(self) -> None:
        object.__setattr__(self, "_frozen", False)
