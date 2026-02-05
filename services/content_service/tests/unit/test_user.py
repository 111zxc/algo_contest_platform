import pytest
from unittest.mock import MagicMock

import app.services.user as user_service


def test_create_user_success(db_session, logger_mock, monkeypatch, simple_obj):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    user_in = simple_obj(
        keycloak_id="kid",
        username="u",
        email="e",
        display_name="d",
        first_name="f",
        last_name="l",
    )

    created = MagicMock()
    def fake_user_ctor(**kwargs):
        assert kwargs["keycloak_id"] == "kid"
        assert kwargs["username"] == "u"
        return created

    monkeypatch.setattr(user_service, "User", fake_user_ctor)

    res = user_service.create_user(db_session, user_in)
    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)
    logger_mock.info.assert_called_once()


def test_get_user_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = user_service.get_user(db_session, "kid")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_get_user_by_username_not_found_returns_none(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = user_service.get_user_by_username(db_session, "name")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_update_user_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    u = MagicMock()
    u.username = "old"
    u.keycloak_id = "kid"

    res = user_service.update_user(db_session, u, {"display_name": "New"})
    assert res is u
    assert u.display_name == "New"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(u)
    logger_mock.info.assert_called_once()


def test_delete_user_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    u = MagicMock()
    u.username = "u"
    u.keycloak_id = "kid"
    user_service.delete_user(db_session, u)

    db_session.delete.assert_called_once_with(u)
    db_session.commit.assert_called_once()
    logger_mock.info.assert_called_once()


def test_get_users_returns_second_query_result(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    q1 = MagicMock()
    q2 = MagicMock()
    q1.all.return_value = ["u1"]
    q2.all.return_value = ["u2", "u3"]

    db_session.query.side_effect = [q1, q2]

    res = user_service.get_users(db_session)
    assert res == ["u2", "u3"]
    logger_mock.info.assert_called_once()


def test_compute_user_rating_sums_balances(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(user_service, "logger", logger_mock)

    balance = MagicMock(side_effect=[1, 2, 10, -1])  # posts(2) + problems(1) + comments(1)
    monkeypatch.setattr(user_service, "compute_reaction_balance", balance)

    post_q = MagicMock(); post_chain = MagicMock()
    post_q.filter.return_value = post_chain
    p1, p2 = MagicMock(), MagicMock()
    p1.id, p2.id = "p1", "p2"
    post_chain.all.return_value = [p1, p2]

    problem_q = MagicMock(); problem_chain = MagicMock()
    problem_q.filter.return_value = problem_chain
    pr = MagicMock(); pr.id = "pr1"
    problem_chain.all.return_value = [pr]

    comment_q = MagicMock(); comment_chain = MagicMock()
    comment_q.filter.return_value = comment_chain
    c = MagicMock(); c.id = "c1"
    comment_chain.all.return_value = [c]

    db_session.query.side_effect = [post_q, problem_q, comment_q]

    rating = user_service.compute_user_rating(db_session, "kid")
    assert rating == (1 + 2) + (10) + (-1)  # 12

    balance.assert_any_call(db_session, "p1", "post")
    balance.assert_any_call(db_session, "p2", "post")
    balance.assert_any_call(db_session, "pr1", "problem")
    balance.assert_any_call(db_session, "c1", "comment")
    logger_mock.info.assert_called_once()
