import pytest
from unittest.mock import MagicMock

import app.services.tag as tag_service


def test_create_tag_success(db_session, logger_mock, monkeypatch, simple_obj):
    tag_in = simple_obj(name="python")
    created = MagicMock()
    def fake_tag_ctor(**kwargs):
        assert kwargs["name"] == "python"
        return created
    monkeypatch.setattr(tag_service, "Tag", fake_tag_ctor)

    res = tag_service.create_tag(db_session, tag_in)
    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)


def test_get_tag_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = tag_service.get_tag(db_session, "tid")
    assert res is None


def test_update_tag_success(db_session, logger_mock, monkeypatch):
    t = MagicMock()
    t.id = "tid"
    t.name = "old"

    res = tag_service.update_tag(db_session, t, {"name": "new"})
    assert res is t
    assert t.name == "new"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(t)


def test_delete_tag_success(db_session, logger_mock, monkeypatch):
    t = MagicMock()
    t.name = "x"
    tag_service.delete_tag(db_session, t)

    db_session.delete.assert_called_once_with(t)
    db_session.commit.assert_called_once()


def test_get_tags_success(db_session, logger_mock, monkeypatch):
    q = MagicMock()
    db_session.query.return_value = q
    q.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    res = tag_service.get_tags(db_session)
    assert len(res) == 3
