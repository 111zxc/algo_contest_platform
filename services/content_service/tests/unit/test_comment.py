import pytest
from unittest.mock import MagicMock

import app.services.comment as comment_service


def test_create_comment_success(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    comment_in = simple_obj(
        post_id="post1",
        content="hi",
        parent_comment_id=None,
    )

    created = MagicMock(name="CommentInstance")
    def fake_comment_ctor(**kwargs):
        assert kwargs["post_id"] == "post1"
        assert kwargs["created_by"] == "u1"
        assert kwargs["content"] == "hi"
        assert kwargs["parent_comment_id"] is None
        return created

    monkeypatch.setattr(comment_service, "Comment", fake_comment_ctor)

    res = comment_service.create_comment(db_session, comment_in, user_id="u1")

    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()
    logger_mock.error.assert_not_called()


def test_create_comment_commit_error_rolls_back(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    comment_in = simple_obj(post_id="p", content="x", parent_comment_id=None)
    created = MagicMock()
    monkeypatch.setattr(comment_service, "Comment", lambda **kwargs: created)

    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        comment_service.create_comment(db_session, comment_in, user_id="u1")

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_get_comment_found(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    c = MagicMock()
    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = c

    res = comment_service.get_comment(db_session, "cid")

    assert res is c
    logger_mock.info.assert_called_once()
    logger_mock.warning.assert_not_called()


def test_get_comment_not_found(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = comment_service.get_comment(db_session, "cid")

    assert res is None
    logger_mock.warning.assert_called_once()


def test_get_comment_query_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock()
    q.filter.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        comment_service.get_comment(db_session, "cid")

    logger_mock.error.assert_called_once()


def test_update_comment_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"

    res = comment_service.update_comment(db_session, c, {"content": "new"})

    assert res is c
    assert c.content == "new"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(c)
    logger_mock.info.assert_called_once()
    db_session.rollback.assert_not_called()


def test_update_comment_commit_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        comment_service.update_comment(db_session, c, {"content": "x"})

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_delete_comment_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"

    comment_service.delete_comment(db_session, c)

    db_session.delete.assert_called_once_with(c)
    db_session.commit.assert_called_once()
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()


def test_delete_comment_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    c = MagicMock()
    c.id = "cid"
    db_session.delete.side_effect = Exception("nope")

    with pytest.raises(Exception):
        comment_service.delete_comment(db_session, c)

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()
    db_session.commit.assert_not_called()


def test_list_comments_by_post_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock()]

    res = comment_service.list_comments_by_post(db_session, "pid")
    assert len(res) == 2
    logger_mock.info.assert_called_once()


def test_list_comments_by_user_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [MagicMock()]

    res = comment_service.list_comments_by_user(db_session, "uid")
    assert len(res) == 1
    logger_mock.info.assert_called_once()


def test_list_enriched_comments_by_post_sets_fields_and_calls_balance(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock(name="query")
    chain = MagicMock(name="chain")
    db_session.query.return_value = q

    q.join.return_value = chain
    chain.filter.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain

    c1, c2 = MagicMock(), MagicMock()
    c1.id, c2.id = "c1", "c2"
    chain.all.return_value = [(c1, "Alice"), (c2, "Bob")]

    balance_fn = MagicMock(side_effect=[10, -2])
    monkeypatch.setattr(comment_service, "compute_reaction_balance", balance_fn)

    res = comment_service.list_enriched_comments_by_post(db_session, "pid", offset=0, limit=10)

    assert res == [c1, c2]
    assert getattr(c1, "author_display_name") == "Alice"
    assert getattr(c1, "reaction_balance") == 10
    assert getattr(c2, "author_display_name") == "Bob"
    assert getattr(c2, "reaction_balance") == -2

    balance_fn.assert_any_call(db_session, "c1", "comment")
    balance_fn.assert_any_call(db_session, "c2", "comment")
    logger_mock.info.assert_called_once()


def test_list_enriched_comments_by_post_query_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(comment_service, "logger", logger_mock)

    q = MagicMock()
    q.join.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        comment_service.list_enriched_comments_by_post(db_session, "pid")

    logger_mock.error.assert_called_once()
