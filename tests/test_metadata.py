import pytest
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.types import ObjectDoesNotExistError
from sqlalchemy_file.helpers import get_content_from_file_obj
from sqlalchemy_file.storage import StorageManager

from tests.utils import get_test_container


class TestMetadata:
    def setup_method(self, method) -> None:
        StorageManager._clear()
        StorageManager.add_storage("test", get_test_container("test-metadata"))

    def test_add_metadata(self):
        name = "test_metadata.txt"
        stored_file = StorageManager.save_file(
            name,
            get_content_from_file_obj(b"Test metadata"),
            metadata={"content_type": "text/plain", "filename": "test_metadata.txt"},
        )
        if isinstance(stored_file.object.driver, LocalStorageDriver):
            assert (
                stored_file.object.container.get_object(f"{name}.metadata.json")
                is not None
            )
        else:
            with pytest.raises(ObjectDoesNotExistError):
                stored_file.object.container.get_object(f"{name}.metadata.json")
        assert stored_file.filename == "test_metadata.txt"
        assert stored_file.content_type == "text/plain"
        StorageManager.delete_file("test/test_metadata.txt")
        with pytest.raises(ObjectDoesNotExistError):
            StorageManager.get().get_object("test_metadata.txt.metadata.json")

    def test_no_metadata(self):
        name = "test_metadata.txt"
        stored_file = StorageManager.save_file(
            name, get_content_from_file_obj(b"Test metadata")
        )
        with pytest.raises(ObjectDoesNotExistError):
            stored_file.object.container.get_object(f"{name}.metadata.json")
        assert stored_file.filename == "unnamed"
        assert stored_file.content_type == "application/octet-stream"
        StorageManager.delete_file("test/test_metadata.txt")

    def teardown_method(self, method):
        StorageManager.get().delete()
