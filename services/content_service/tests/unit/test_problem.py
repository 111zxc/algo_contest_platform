import pytest
from unittest.mock import MagicMock

import app.services.problem as problem_service


def test_create_problem_converts_test_cases_to_dicts(db_session, logger_mock, monkeypatch, simple_obj):
    tc1 = MagicMock()
    tc1.to_dict.return_value = {"a": 1}
    tc2 = MagicMock()
    tc2.to_dict.return_value = {"b": 2}

    problem_in = simple_obj(
        title="T",
        description="D",
        difficulty="EASY",
        test_cases=[tc1, tc2],
        time_limit=1,
        memory_limit=64,
        contest_id=None,
    )

    created = MagicMock()
    def fake_problem_ctor(**kwargs):
        assert kwargs["test_cases"] == [{"a": 1}, {"b": 2}]
        assert kwargs["created_by"] == "u1"
        return created

    monkeypatch.setattr(problem_service, "Problem", fake_problem_ctor)

    res = problem_service.create_problem(db_session, problem_in, creator_id="u1")

    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)


def test_create_problem_commit_error_rolls_back(db_session, logger_mock, monkeypatch, simple_obj):
    problem_in = simple_obj(
        title="T", description="D", difficulty="EASY",
        test_cases=None, time_limit=1, memory_limit=64, contest_id=None
    )
    created = MagicMock()
    monkeypatch.setattr(problem_service, "Problem", lambda **kwargs: created)
    db_session.commit.side_effect = RuntimeError("fail")

    with pytest.raises(RuntimeError):
        problem_service.create_problem(db_session, problem_in, creator_id="u1")

    db_session.rollback.assert_called_once()


def test_get_problem_found_uses_joinedload(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(problem_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.options.return_value = chain
    obj = MagicMock()
    chain.first.return_value = obj

    res = problem_service.get_problem(db_session, "pid")
    assert res is obj
    chain.options.assert_called_once()


def test_update_problem_skips_tags(db_session, logger_mock, monkeypatch):
    p = MagicMock()
    p.id = "pid"
    p.tags = ["old"]

    res = problem_service.update_problem(db_session, p, {"title": "new", "tags": ["x"]})
    assert res is p
    assert p.title == "new"
    assert p.tags == ["old"]

    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(p)


def test_delete_problem_success(db_session, logger_mock, monkeypatch):
    p = MagicMock()
    p.id = "pid"

    problem_service.delete_problem(db_session, p)

    db_session.delete.assert_called_once_with(p)
    db_session.commit.assert_called_once()


def test_list_problems_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(problem_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock()]

    res = problem_service.list_problems(db_session)
    assert len(res) == 2


def test_list_problems_by_tag_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(problem_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock()]

    res = problem_service.list_problems_by_tag(db_session, "tag1")
    assert len(res) == 1


def test_list_problems_by_user_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(problem_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock(), MagicMock()]

    res = problem_service.list_problems_by_user(db_session, "u1")
    assert len(res) == 2


def test_list_problems_by_difficulty_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(problem_service, "joinedload", lambda *args, **kwargs: object())

    q = MagicMock()
    chain = MagicMock()
    chain2 = MagicMock()
    db_session.query.return_value = q
    q.options.return_value = chain
    chain.filter.return_value = chain2
    chain2.all.return_value = [MagicMock()]

    res = problem_service.list_problems_by_difficulty(db_session, "EASY")
    assert len(res) == 1


def test_list_enriched_problems_filtered_sets_fields_and_filters_contest_none(db_session, logger_mock, monkeypatch):
    subq = MagicMock()
    subq.c = MagicMock()
    subq.c.balance = MagicMock()
    subq.c.problem_id = MagicMock()

    build_q = MagicMock()
    build_chain = MagicMock()
    build_q.filter.return_value = build_chain
    build_chain.group_by.return_value = build_chain
    build_chain.subquery.return_value = subq

    class _FakeOrder:
        def __init__(self):
            self.asc_called = False
            self.desc_called = False
        def asc(self):
            self.asc_called = True
            return "ASC"
        def desc(self):
            self.desc_called = True
            return "DESC"
    fake_order = _FakeOrder()
    monkeypatch.setattr(problem_service.func, "coalesce", lambda *args, **kwargs: fake_order)

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
    main_chain.order_by.return_value = main_chain
    main_chain.offset.return_value = main_chain
    main_chain.limit.return_value = main_chain

    pr1, pr2 = MagicMock(), MagicMock()
    pr1.id, pr2.id = "pr1", "pr2"
    main_chain.all.return_value = [(pr1, "Alice", None), (pr2, "Bob", 2)]

    res = problem_service.list_enriched_problems_filtered(
        db_session,
        offset=0,
        limit=10,
        difficulty="EASY",
        tag_id="tag1",
        sort_by_rating=True,
        sort_order="asc",
    )

    assert res == [pr1, pr2]
    assert pr1.author_display_name == "Alice"
    assert pr1.reaction_balance == 0
    assert pr2.author_display_name == "Bob"
    assert pr2.reaction_balance == 2

    assert fake_order.asc_called is True

    assert main_chain.filter.call_count >= 2  # difficulty/tag/contest_id


def test_list_enriched_problems_filtered_subquery_error_raises(db_session, logger_mock, monkeypatch):
    db_session.query.side_effect = Exception("boom")

    with pytest.raises(Exception):
        problem_service.list_enriched_problems_filtered(db_session)
