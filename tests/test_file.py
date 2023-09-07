import pytest
from sqlalchemy_file.file import File


def test_file_missing_content():
    with pytest.raises(
        ValueError, match="Either content or content_path must be specified"
    ):
        File()
