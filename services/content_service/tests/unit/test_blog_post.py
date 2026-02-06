import pytest
from unittest.mock import MagicMock

import app.services.blog_post as blog_post_service


def _make_query_chain(first_result=None, all_result=None):
    """
    Возвращает (query_mock, chain_mock) для подстановки в db.query().
    - first_result: что вернёт .first()
    - all_result: что вернёт .all()
    """
    q = MagicMock(name="query")
    chain = MagicMock(name="chain")

    q.filter.return_value = chain
    chain.first.return_value = first_result

    q.order_by.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain
    chain.all.return_value = all_result if all_result is not None else []

    return q, chain


def test_create_blog_post_success(db_session, simple_obj, logger_mock, monkeypatch):
    data = simple_obj(title="Hello", description="World")

    post_obj = MagicMock(name="BlogPostInstance")
    def fake_blogpost_ctor(title, description):
        assert title == "Hello"
        assert description == "World"
        return post_obj

    monkeypatch.setattr(blog_post_service, "BlogPost", fake_blogpost_ctor)

    res = blog_post_service.create_blog_post(db_session, data)

    assert res is post_obj
    db_session.add.assert_called_once_with(post_obj)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(post_obj)
    db_session.rollback.assert_not_called()


def test_create_blog_post_commit_error_rolls_back(db_session, simple_obj, logger_mock, monkeypatch):
    data = simple_obj(title="Bad", description="Commit")
    post_obj = MagicMock(name="BlogPostInstance")
    monkeypatch.setattr(blog_post_service, "BlogPost", lambda title, description: post_obj)

    db_session.commit.side_effect = RuntimeError("db down")

    with pytest.raises(RuntimeError):
        blog_post_service.create_blog_post(db_session, data)

    db_session.rollback.assert_called_once()


def test_get_blog_post_found(db_session, logger_mock, monkeypatch):
    post = MagicMock(name="Post")
    q, chain = _make_query_chain(first_result=post)
    db_session.query.return_value = q

    res = blog_post_service.get_blog_post(db_session, "pid")

    assert res is post
    db_session.query.assert_called_once()
    q.filter.assert_called_once()
    chain.first.assert_called_once()


def test_get_blog_post_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    q, chain = _make_query_chain(first_result=None)
    db_session.query.return_value = q

    res = blog_post_service.get_blog_post(db_session, "pid")

    assert res is None


def test_get_blog_post_query_error_raises(db_session, logger_mock, monkeypatch):
    q = MagicMock()
    q.filter.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        blog_post_service.get_blog_post(db_session, "pid")


def test_update_blog_post_success(db_session, logger_mock, monkeypatch):
    post = MagicMock(name="Post")
    post.id = "pid"

    res = blog_post_service.update_blog_post(db_session, post, {"title": "New", "description": "Desc"})

    assert res is post
    assert post.title == "New"
    assert post.description == "Desc"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(post)
    db_session.rollback.assert_not_called()


def test_update_blog_post_commit_error_rolls_back(db_session, logger_mock, monkeypatch):
    post = MagicMock()
    post.id = "pid"
    db_session.commit.side_effect = RuntimeError("commit fail")

    with pytest.raises(RuntimeError):
        blog_post_service.update_blog_post(db_session, post, {"title": "X"})

    db_session.rollback.assert_called_once()


def test_delete_blog_post_success(db_session, logger_mock, monkeypatch):
    post = MagicMock()
    post.id = "pid"

    blog_post_service.delete_blog_post(db_session, post)

    db_session.delete.assert_called_once_with(post)
    db_session.commit.assert_called_once()
    db_session.rollback.assert_not_called()


def test_delete_blog_post_delete_error_rolls_back(db_session, logger_mock, monkeypatch):
    post = MagicMock()
    post.id = "pid"
    db_session.delete.side_effect = Exception("nope")

    with pytest.raises(Exception):
        blog_post_service.delete_blog_post(db_session, post)

    db_session.rollback.assert_called_once()
    db_session.commit.assert_not_called()


def test_list_blog_posts_success(db_session, logger_mock, monkeypatch):
    posts = [MagicMock(), MagicMock()]
    q, chain = _make_query_chain(all_result=posts)
    db_session.query.return_value = q

    res = blog_post_service.list_blog_posts(db_session, offset=5, limit=2)

    assert res == posts
    q.order_by.assert_called_once()
    chain.offset.assert_called_once_with(5)
    chain.limit.assert_called_once_with(2)
    chain.all.assert_called_once()


def test_list_blog_posts_query_error_raises(db_session, logger_mock, monkeypatch):
    q = MagicMock()
    q.order_by.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        blog_post_service.list_blog_posts(db_session)
