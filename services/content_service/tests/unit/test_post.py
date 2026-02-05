import pytest
from unittest.mock import MagicMock

import app.services.post as post_service


def test_create_post_success(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post_in = simple_obj(
        problem_id="pr1",
        title="t",
        content="c",
        language="py",
        status="DRAFT",
    )

    created = MagicMock(name="PostInstance")
    def fake_post_ctor(**kwargs):
        assert kwargs["problem_id"] == "pr1"
        assert kwargs["created_by"] == "u1"
        assert kwargs["title"] == "t"
        assert kwargs["content"] == "c"
        assert kwargs["language"] == "py"
        assert kwargs["status"] == "DRAFT"
        return created

    monkeypatch.setattr(post_service, "Post", fake_post_ctor)

    res = post_service.create_post(db_session, post_in, user_id="u1")

    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()
    logger_mock.error.assert_not_called()


def test_create_post_commit_error_rolls_back(db_session, simple_obj, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post_in = simple_obj(problem_id="pr1", title="t", content="c", language="py", status="DRAFT")
    created = MagicMock()
    monkeypatch.setattr(post_service, "Post", lambda **kwargs: created)
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        post_service.create_post(db_session, post_in, user_id="u1")

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_get_post_found_uses_joinedload(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    jl = object()
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: jl)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.options.return_value = chain

    post = MagicMock()
    chain.first.return_value = post

    res = post_service.get_post(db_session, "pid")
    assert res is post

    chain.options.assert_called_once()
    logger_mock.info.assert_called_once()
    logger_mock.warning.assert_not_called()


def test_get_post_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.options.return_value = chain
    chain.first.return_value = None

    res = post_service.get_post(db_session, "pid")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_get_post_query_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    q.filter.side_effect = Exception("boom")
    db_session.query.return_value = q

    with pytest.raises(Exception):
        post_service.get_post(db_session, "pid")
    logger_mock.error.assert_called_once()


def test_update_post_skips_tags(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post = MagicMock()
    post.id = "pid"
    post.tags = ["old"]

    res = post_service.update_post(db_session, post, {"title": "new", "tags": ["x"]})
    assert res is post
    assert post.title == "new"
    assert post.tags == ["old"]

    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(post)
    logger_mock.info.assert_called_once()


def test_update_post_commit_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post = MagicMock()
    post.id = "pid"
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        post_service.update_post(db_session, post, {"title": "x"})

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_delete_post_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post = MagicMock()
    post.id = "pid"

    post_service.delete_post(db_session, post)

    db_session.delete.assert_called_once_with(post)
    db_session.commit.assert_called_once()
    db_session.rollback.assert_not_called()
    logger_mock.info.assert_called_once()


def test_delete_post_error_rolls_back(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    post = MagicMock()
    post.id = "pid"
    db_session.delete.side_effect = Exception("nope")

    with pytest.raises(Exception):
        post_service.delete_post(db_session, post)

    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()
    db_session.commit.assert_not_called()


def test_list_posts_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock()]

    res = post_service.list_posts(db_session)
    assert len(res) == 2
    q.options.assert_called_once()
    logger_mock.info.assert_called_once()


def test_list_posts_by_user_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock()]

    res = post_service.list_posts_by_user(db_session, "u1")
    assert len(res) == 1
    logger_mock.info.assert_called_once()


def test_list_posts_by_problem_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    res = post_service.list_posts_by_problem(db_session, "pr1")
    assert len(res) == 3
    logger_mock.info.assert_called_once()


def test_list_posts_by_tag_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    monkeypatch.setattr(post_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock()]

    res = post_service.list_posts_by_tag(db_session, "tag1")
    assert len(res) == 1
    logger_mock.info.assert_called_once()


def test_list_enriched_posts_by_problem_sets_fields_and_defaults_balance(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    subq = MagicMock(name="reaction_subq")
    subq.c = MagicMock()
    subq.c.balance = MagicMock(name="balance_col")
    subq.c.post_id = MagicMock(name="post_id_col")

    build_q = MagicMock(name="build_subq_query")
    build_chain = MagicMock(name="build_subq_chain")
    db_session.query.return_value = build_q
    build_q.filter.return_value = build_chain
    build_chain.group_by.return_value = build_chain
    build_chain.subquery.return_value = subq

    class _FakeOrder:
        def __init__(self):
            self.asc_called = False
            self.desc_called = False
        def asc(self):
            self.asc_called = True
            return "ASC_EXPR"
        def desc(self):
            self.desc_called = True
            return "DESC_EXPR"

    fake_order = _FakeOrder()
    monkeypatch.setattr(post_service.func, "coalesce", lambda *args, **kwargs: fake_order)

    main_q = MagicMock(name="main_query")
    main_chain = MagicMock(name="main_chain")

    def query_side_effect(*args, **kwargs):
        if query_side_effect.calls == 0:
            query_side_effect.calls += 1
            return build_q
        return main_q
    query_side_effect.calls = 0
    db_session.query.side_effect = query_side_effect

    main_q.join.return_value = main_chain
    main_chain.outerjoin.return_value = main_chain
    main_chain.filter.return_value = main_chain
    main_chain.order_by.return_value = main_chain
    main_chain.offset.return_value = main_chain
    main_chain.limit.return_value = main_chain

    p1, p2 = MagicMock(), MagicMock()
    p1.id, p2.id = "p1", "p2"
    main_chain.all.return_value = [(p1, "Alice", None), (p2, "Bob", 5)]

    res = post_service.list_enriched_posts_by_problem(
        db_session,
        problem_id="pr1",
        offset=0,
        limit=10,
        tag_id=None,
        sort_by_rating=True,
        sort_order="desc",
    )

    assert res == [p1, p2]
    assert p1.author_display_name == "Alice"
    assert p1.reaction_balance == 0  # None -> 0
    assert p2.author_display_name == "Bob"
    assert p2.reaction_balance == 5

    assert fake_order.desc_called is True
    logger_mock.info.assert_called_once()


def test_list_enriched_posts_by_problem_applies_tag_filter(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)

    subq = MagicMock()
    subq.c = MagicMock()
    subq.c.balance = MagicMock()
    subq.c.post_id = MagicMock()

    build_q = MagicMock()
    build_chain = MagicMock()
    build_q.filter.return_value = build_chain
    build_chain.group_by.return_value = build_chain
    build_chain.subquery.return_value = subq

    main_q = MagicMock()
    main_chain = MagicMock()
    def query_side_effect(*args, **kwargs):
        if query_side_effect.calls == 0:
            query_side_effect.calls += 1
            return build_q
        return main_q
    query_side_effect.calls = 0
    db_session.query.side_effect = query_side_effect

    main_q.join.return_value = main_chain
    main_chain.outerjoin.return_value = main_chain
    main_chain.filter.return_value = main_chain
    main_chain.offset.return_value = main_chain
    main_chain.limit.return_value = main_chain
    main_chain.all.return_value = []

    post_service.list_enriched_posts_by_problem(
        db_session, "pr1", tag_id="tag1", sort_by_rating=False
    )

    assert main_chain.filter.call_count >= 2
    logger_mock.info.assert_called_once()


def test_list_enriched_posts_by_problem_subquery_error_raises(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(post_service, "logger", logger_mock)
    db_session.query.side_effect = Exception("boom")

    with pytest.raises(Exception):
        post_service.list_enriched_posts_by_problem(db_session, "pr1")

    logger_mock.error.assert_called_once()
