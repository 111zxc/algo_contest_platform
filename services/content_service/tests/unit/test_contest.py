import pytest
from unittest.mock import MagicMock

import app.services.contest as contest_service


def test_create_contest_success(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    data = simple_obj(name="C1", description="D", is_public=True)

    contest_obj = MagicMock(name="ContestInstance")
    def fake_contest_ctor(**kwargs):
        assert kwargs["name"] == "C1"
        assert kwargs["description"] == "D"
        assert kwargs["is_public"] is True
        assert kwargs["created_by"] == "owner1"
        return contest_obj

    monkeypatch.setattr(contest_service, "Contest", fake_contest_ctor)

    res = contest_service.create_contest(db_session, data, owner_id="owner1")

    assert res is contest_obj
    db_session.add.assert_called_once_with(contest_obj)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(contest_obj)
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()
    logger_mock.error.assert_not_called()


def test_create_contest_commit_error_rolls_back(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    data = simple_obj(name="C1", description="D", is_public=True)
    contest_obj = MagicMock()
    monkeypatch.setattr(contest_service, "Contest", lambda **kwargs: contest_obj)

    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        contest_service.create_contest(db_session, data, owner_id="o")

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_get_contest_found(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    contest = MagicMock()
    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = contest

    res = contest_service.get_contest(db_session, "cid")
    assert res is contest
    logger_mock.info.assert_called_once()
    logger_mock.warning.assert_not_called()


def test_get_contest_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = contest_service.get_contest(db_session, "cid")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_update_contest_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"

    res = contest_service.update_contest(db_session, c, {"name": "N"})

    assert res is c
    assert c.name == "N"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(c)
    logger_mock.info.assert_called_once()
    db_session.rollback.assert_not_called()


def test_update_contest_commit_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        contest_service.update_contest(db_session, c, {"name": "N"})

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_delete_contest_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"

    contest_service.delete_contest(db_session, c)

    db_session.delete.assert_called_once_with(c)
    db_session.commit.assert_called_once()
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()


def test_delete_contest_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"
    db_session.delete.side_effect = Exception("nope")

    with pytest.raises(Exception):
        contest_service.delete_contest(db_session, c)

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()
    db_session.commit.assert_not_called()


def test_list_public_contests_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q

    q.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    res = contest_service.list_public_contests(db_session, offset=2, limit=3)
    assert len(res) == 3
    chain.offset.assert_called_once_with(2)
    chain.limit.assert_called_once_with(3)
    logger_mock.info.assert_called_once()


def test_list_public_contests_query_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    q = MagicMock()
    q.filter.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        contest_service.list_public_contests(db_session)

    logger_mock.error.assert_called_once()


def test_list_owner_contests_returns_query_chain(db_session):
    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.all.return_value = ["c1"]

    res = contest_service.list_owner_contests(db_session, "owner")
    assert res == ["c1"]


def test_join_public_contest_private_contest_no_commit(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    contest = MagicMock()
    contest.is_public = False
    contest.participants = []

    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)

    contest_service.join_public_contest(db_session, "cid", "uid")

    db_session.commit.assert_not_called()
    logger_mock.error.assert_called_once()


def test_join_public_contest_already_participant_no_commit(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    u = MagicMock()
    u.keycloak_id = "uid"

    contest = MagicMock()
    contest.is_public = True
    contest.participants = [u]

    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)

    contest_service.join_public_contest(db_session, "cid", "uid")

    db_session.commit.assert_not_called()


def test_join_public_contest_success_appends_and_commits(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    contest = MagicMock()
    contest.is_public = True
    contest.participants = []

    user = MagicMock()
    user.keycloak_id = "uid"

    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)
    monkeypatch.setattr(contest_service, "get_user", lambda db, uid: user)

    contest_service.join_public_contest(db_session, "cid", "uid")

    assert contest.participants == [user]
    db_session.commit.assert_called_once()
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()


def test_join_public_contest_commit_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    contest = MagicMock()
    contest.is_public = True
    contest.participants = []

    user = MagicMock()
    user.keycloak_id = "uid"

    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)
    monkeypatch.setattr(contest_service, "get_user", lambda db, uid: user)
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        contest_service.join_public_contest(db_session, "cid", "uid")

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_add_user_to_contest_by_username_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    contest = MagicMock()
    contest.participants = []

    user = MagicMock()
    user.keycloak_id = "kid"
    user.username = "bob"

    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)
    monkeypatch.setattr(contest_service, "get_user_by_username", lambda db, uname: user)

    contest_service.add_user_to_contest_by_username(db_session, "cid", "bob")

    assert contest.participants == [user]
    db_session.commit.assert_called_once()
    logger_mock.info.assert_called_once()


def test_list_contest_participants(db_session, monkeypatch):
    contest = MagicMock()
    contest.participants = ["u1", "u2"]
    monkeypatch.setattr(contest_service, "get_contest", lambda db, cid: contest)

    res = contest_service.list_contest_participants(db_session, "cid")
    assert res == ["u1", "u2"]


def test_list_contest_tasks_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = ["p1", "p2"]

    res = contest_service.list_contest_tasks(db_session, "cid")
    assert res == ["p1", "p2"]
    logger_mock.info.assert_called_once()


def test_list_contest_tasks_query_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    q = MagicMock()
    q.filter.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        contest_service.list_contest_tasks(db_session, "cid")

    logger_mock.error.assert_called_once()


def test_list_user_contests_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    user = MagicMock()
    user.contests_joined = ["c1", "c2"]

    monkeypatch.setattr(contest_service, "get_user", lambda db, uid: user)

    res = contest_service.list_user_contests(db_session, "uid")
    assert res == ["c1", "c2"]
    logger_mock.info.assert_called_once()


def test_list_user_contests_get_user_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(contest_service, "logger", logger_mock)

    def boom(db, uid):
        raise RuntimeError("no user")

    monkeypatch.setattr(contest_service, "get_user", boom)

    with pytest.raises(RuntimeError):
        contest_service.list_user_contests(db_session, "uid")

    logger_mock.error.assert_called_once()
