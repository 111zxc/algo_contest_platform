import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException

import app.services.keycloak as keycloak_service


class DummySettings:
    KEYCLOAK_URL = "http://kc"
    KEYCLOAK_ADMIN = "admin"
    KEYCLOAK_ADMIN_PASSWORD = "pass"
    KEYCLOAK_REALM = "realm1"


def test_get_keycloak_admin_token_success(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": "TOKEN"}
    post = MagicMock(return_value=resp)
    monkeypatch.setattr(keycloak_service.requests, "post", post)

    token = keycloak_service.get_keycloak_admin_token()

    assert token == "TOKEN"
    post.assert_called_once()
    logger_mock.debug.assert_called_once()


def test_get_keycloak_admin_token_requests_error_raises(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    def boom(*args, **kwargs):
        raise RuntimeError("net")

    monkeypatch.setattr(keycloak_service.requests, "post", boom)

    with pytest.raises(RuntimeError):
        keycloak_service.get_keycloak_admin_token()

    logger_mock.error.assert_called_once()


def test_get_keycloak_admin_token_bad_status_raises_http_exception(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 401
    resp.text = "unauthorized"
    monkeypatch.setattr(keycloak_service.requests, "post", MagicMock(return_value=resp))

    with pytest.raises(HTTPException) as exc:
        keycloak_service.get_keycloak_admin_token()

    assert exc.value.status_code == 500


def test_register_user_in_keycloak_success_201(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 201
    resp.text = "ok"
    resp.headers = {"Location": "http://kc/admin/realms/realm1/users/abc123"}
    post = MagicMock(return_value=resp)
    monkeypatch.setattr(keycloak_service.requests, "post", post)

    kid = keycloak_service.register_user_in_keycloak({"u": 1}, admin_token="T")

    assert kid == "abc123"
    logger_mock.info.assert_called_once()


def test_register_user_in_keycloak_success_204(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 204
    resp.text = ""
    resp.headers = {"Location": "http://kc/x/y/z/user-id-999/"}
    monkeypatch.setattr(keycloak_service.requests, "post", MagicMock(return_value=resp))

    kid = keycloak_service.register_user_in_keycloak({"u": 1}, admin_token="T")
    assert kid == "user-id-999"


def test_register_user_in_keycloak_requests_error_raises(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    def boom(*args, **kwargs):
        raise RuntimeError("net")

    monkeypatch.setattr(keycloak_service.requests, "post", boom)

    with pytest.raises(RuntimeError):
        keycloak_service.register_user_in_keycloak({"u": 1}, admin_token="T")

    logger_mock.error.assert_called_once()


def test_register_user_in_keycloak_bad_status_raises_http_exception(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 400
    resp.text = "bad request"
    resp.headers = {}
    monkeypatch.setattr(keycloak_service.requests, "post", MagicMock(return_value=resp))

    with pytest.raises(HTTPException) as exc:
        keycloak_service.register_user_in_keycloak({"u": 1}, admin_token="T")

    assert exc.value.status_code == 500
    logger_mock.warning.assert_called_once()


def test_register_user_in_keycloak_missing_location_raises_http_exception(logger_mock, monkeypatch):
    monkeypatch.setattr(keycloak_service, "logger", logger_mock)
    monkeypatch.setattr(keycloak_service, "settings", DummySettings)

    resp = MagicMock()
    resp.status_code = 201
    resp.text = "ok"
    resp.headers = {}
    monkeypatch.setattr(keycloak_service.requests, "post", MagicMock(return_value=resp))

    with pytest.raises(HTTPException) as exc:
        keycloak_service.register_user_in_keycloak({"u": 1}, admin_token="T")

    assert exc.value.status_code == 500
    logger_mock.warning.assert_called_once()
