import pytest
from sqlalchemy_file.storage import StorageManager

from tests.utils import get_dummy_container


class TestStorageManager:
    def setup_method(self, method) -> None:
        StorageManager._clear()

    def test_get_storage_and_file_id(self) -> None:
        assert StorageManager._get_storage_and_file_id("storage/file") == ("storage", "file")
        assert StorageManager._get_storage_and_file_id("storage/folder/file") == ("storage/folder", "file")

    def test_first_configured_is_default(self) -> None:
        StorageManager.add_storage("first", get_dummy_container("first"))
        StorageManager.add_storage("second", get_dummy_container("second"))
        assert StorageManager.get_default() == "first"

    def test_changing_default_storage_works(self) -> None:
        StorageManager.add_storage("first", get_dummy_container("first"))
        StorageManager.add_storage("second", get_dummy_container("second"))
        StorageManager.set_default("second")
        assert StorageManager.get_default() == "second"

    def test_complex_storage_name(self) -> None:
        StorageManager.add_storage("storage/folder", get_dummy_container("storage/folder"))
        StorageManager.add_storage("storage/folder/subfolder", get_dummy_container("storage/folder/subfolder"))
        assert StorageManager.get_default() == "storage/folder"

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

    def test_save_file_missing_content(self):
        with pytest.raises(
            ValueError, match="Either content or content_path must be specified"
        ):
            StorageManager.save_file("id")
