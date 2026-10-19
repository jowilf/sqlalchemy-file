import os

import pytest
from libcloud.storage.drivers.local import LocalStorageDriver
from libcloud.storage.drivers.minio import MinIOStorageDriver
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from tests.utils import get_or_create_container

try:
    from testcontainers.community.minio import MinioContainer
    from testcontainers.community.mysql import MySqlContainer
    from testcontainers.community.postgres import PostgresContainer
except ImportError:  # pragma: no cover
    try:
        from testcontainers.minio import MinioContainer
        from testcontainers.mysql import MySqlContainer
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        MinioContainer = MySqlContainer = PostgresContainer = None  # type: ignore[assignment,misc]

_MINIO_KEY = "minioadmin"
_MINIO_SECRET = "minioadmin"
_MINIO_IMAGE = "ghcr.io/coollabsio/minio"
_DATABASE_CONTAINERS = {"mysql": "mysql_container", "postgres": "postgres_container"}


def _selected_params(params: tuple[str, ...], subset_env: str) -> tuple[str, ...]:
    """Reduce *params* to the comma-separated backends exported in *subset_env*."""
    override = os.environ.get(subset_env)
    if not override:
        return params
    selected = {value.strip() for value in override.split(",")}  # pragma: no cover
    return (
        tuple(param for param in params if param in selected) or params
    )  # pragma: no cover


@pytest.fixture(scope="session")
def mysql_container():
    """MySQL container shared by the whole test session."""
    with MySqlContainer(  # pragma: no cover
        "mysql:8.0", dialect="pymysql", username="test", password="test", dbname="test"
    ) as container:
        yield container


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL container shared by the whole test session."""
    with PostgresContainer(  # pragma: no cover
        "postgres:15", username="test", password="test", dbname="test"
    ) as container:
        yield container


@pytest.fixture(scope="session")
def minio_container():
    """MinIO container shared by the whole test session."""
    with MinioContainer(  # pragma: no cover
        image=_MINIO_IMAGE, access_key=_MINIO_KEY, secret_key=_MINIO_SECRET
    ) as container:
        yield container


@pytest.fixture(scope="session")
def _minio_libcloud_driver(minio_container):
    """Libcloud MinIO driver bound to the session-scoped MinIO container."""
    endpoint = minio_container.get_config()["endpoint"]  # pragma: no cover
    host, _, port_str = endpoint.partition(":")  # pragma: no cover
    return MinIOStorageDriver(  # pragma: no cover
        key=_MINIO_KEY,
        secret=_MINIO_SECRET,
        host=host,
        port=int(port_str),
        secure=False,
    )


def get_engine_url(
    request: pytest.FixtureRequest, backend: str
) -> str:  # pragma: no cover
    """Connection URL of the requested database backend.

    Container-backed backends are started once per session, on first use.
    """
    if backend == "sqlite":
        return "sqlite:///:memory:?check_same_thread=False"
    return request.getfixturevalue(_DATABASE_CONTAINERS[backend]).get_connection_url()


@pytest.fixture(params=_selected_params(("sqlite", "mysql", "postgres"), "TEST_DB"))
def sqla_backend(request: pytest.FixtureRequest):
    """Parametrized database backend for the SQLA integration tests."""
    yield request.param


@pytest.fixture
def engine(request: pytest.FixtureRequest, sqla_backend: str) -> Engine:
    """Yield a fresh SQLAlchemy engine for the current ``sqla_backend``.

    Tests inject it directly as a parameter (``def test_x(engine)``); the
    per-module autouse ``sqla_storage`` fixtures request it for schema
    setup, so a single engine instance is shared by each test.
    """
    engine = create_engine(get_engine_url(request, sqla_backend))
    yield engine
    engine.dispose()


@pytest.fixture
def sqla_storage_factory(sqla_backend, tmp_path, _minio_libcloud_driver):
    """Backend-aware storage factory.

    SQLite tests exercise the MinIO code path; MySQL and PostgreSQL tests
    use the local driver to avoid a second container.
    """
    if sqla_backend == "sqlite":
        driver = _minio_libcloud_driver
    else:
        driver = LocalStorageDriver(str(tmp_path))
    yield lambda name: get_or_create_container(driver, name)
