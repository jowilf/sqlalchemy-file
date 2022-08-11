import pytest
from sqlalchemy_file.storage import StorageManager

from tests.utils import get_dummy_container


class TestStorageManager:
    def setup(self) -> None:
        StorageManager._clear()

    def test_first_configured_is_default(self) -> None:
        StorageManager.add_storage("first", get_dummy_container("first"))
        StorageManager.add_storage("second", get_dummy_container("second"))
        assert StorageManager.get_default() == "first"

    def test_changing_default_storage_works(self) -> None:
        StorageManager.add_storage("first", get_dummy_container("first"))
        StorageManager.add_storage("second", get_dummy_container("second"))
        StorageManager.set_default("second")
        assert StorageManager.get_default() == "second"

    def test_no_storage_is_detected(self) -> None:
        with pytest.raises(RuntimeError):
            StorageManager.get_default()
        with pytest.raises(RuntimeError):
            StorageManager.get()

    def test_prevent_non_existing_default(self) -> None:
        with pytest.raises(RuntimeError):
            StorageManager.set_default("does_not_exists")

    def test_prevent_non_existing(self) -> None:
        with pytest.raises(RuntimeError):
            StorageManager.get("does_not_exists")

    def test_unique_storage_name(self) -> None:
        StorageManager.add_storage("first", get_dummy_container("first"))
        with pytest.raises(RuntimeError):
            StorageManager.add_storage("first", get_dummy_container("second"))
