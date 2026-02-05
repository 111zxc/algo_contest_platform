import types
import sys
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def db_session():
    return MagicMock(name="db_session")


@pytest.fixture
def logger_mock():
    return MagicMock(name="logger")


@pytest.fixture
def simple_obj():
    def _factory(**kwargs):
        return type("Obj", (), kwargs)()
    return _factory


def pytest_sessionstart(session):
    fake_db = types.ModuleType("app.core.database")
    fake_db.SessionLocal = MagicMock(name="SessionLocal")
    sys.modules["app.core.database"] = fake_db