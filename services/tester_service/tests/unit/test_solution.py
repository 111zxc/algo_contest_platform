import pytest
from unittest.mock import MagicMock

import app.services.solution as solution_service


class DummySettings:
    CONTENT_SERVICE_URL = "http://content"


def test_create_solution_sets_pending(db_session, logger_mock, monkeypatch, simple_obj):
    monkeypatch.setattr(solution_service, "logger", logger_mock)

    solution_in = simple_obj(problem_id="p1", code="c", language="python")

    created = MagicMock()
    def fake_solution_ctor(**kwargs):
        assert kwargs["created_by"] == "u1"
        assert kwargs["problem_id"] == "p1"
        assert kwargs["status"] == solution_service.SolutionStatus.PENDING
        return created

    monkeypatch.setattr(solution_service, "Solution", fake_solution_ctor)

    res = solution_service.create_solution(db_session, solution_in, user_id="u1")
    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)
    logger_mock.info.assert_called_once()


def test_get_solution_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(solution_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = solution_service.get_solution(db_session, "sid")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_update_solution_status_missing_solution_returns_none(db_session, monkeypatch):
    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: None)

    res = solution_service.update_solution_status(db_session, "sid", {"status": "AC"})
    assert res is None


def test_update_solution_status_commit_error_rolls_back_and_returns_none(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(solution_service, "logger", logger_mock)

    sol = MagicMock()
    sol.id = "sid"
    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: sol)

    db_session.commit.side_effect = Exception("fail")

    res = solution_service.update_solution_status(db_session, "sid", {"status": "AC", "time_used": 1})
    assert res is None
    db_session.rollback.assert_called_once()
    logger_mock.error.assert_called_once()


def test_process_solution_solution_not_found_updates_status_and_returns_error(monkeypatch, logger_mock):
    monkeypatch.setattr(solution_service, "logger", logger_mock)
    monkeypatch.setattr(solution_service, "settings", DummySettings)

    db = MagicMock()
    monkeypatch.setattr(solution_service, "SessionLocal", lambda: db)

    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: None)

    upd = MagicMock()
    monkeypatch.setattr(solution_service, "update_solution_status", upd)

    res = solution_service.process_solution("sid")
    assert res == {"error": "Solution not found"}
    upd.assert_called_once()
    db.close.assert_called_once()


def test_process_solution_problem_not_found(monkeypatch, logger_mock):
    monkeypatch.setattr(solution_service, "logger", logger_mock)
    monkeypatch.setattr(solution_service, "settings", DummySettings)

    db = MagicMock()
    monkeypatch.setattr(solution_service, "SessionLocal", lambda: db)

    sol = MagicMock()
    sol.problem_id = "p1"
    sol.created_by = "u1"
    sol.code = "code"
    sol.language = "python"
    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: sol)

    resp = MagicMock()
    resp.status_code = 404
    monkeypatch.setattr(solution_service.requests, "get", lambda url: resp)

    upd = MagicMock()
    monkeypatch.setattr(solution_service, "update_solution_status", upd)

    res = solution_service.process_solution("sid")
    assert res == {"error": "Problem not found"}
    upd.assert_called_once()
    db.close.assert_called_once()


def test_process_solution_AC_sets_faster_than_and_marks_solved(monkeypatch, logger_mock):
    monkeypatch.setattr(solution_service, "logger", logger_mock)
    monkeypatch.setattr(solution_service, "settings", DummySettings)

    db = MagicMock()
    monkeypatch.setattr(solution_service, "SessionLocal", lambda: db)

    sol = MagicMock()
    sol.problem_id = "p1"
    sol.created_by = "u1"
    sol.code = "code"
    sol.language = "python"
    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: sol)

    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.json.return_value = {
        "test_cases": [{"input_data": "1", "output_data": "2"}],
        "time_limit": 3,
        "memory_limit": 64,
    }
    monkeypatch.setattr(solution_service.requests, "get", lambda url: get_resp)

    monkeypatch.setattr(
        solution_service,
        "run_solution_in_container",
        lambda code, lang, tcs, tl, ml: {"status": "AC", "results": [{"time_used": 0.42}], "time_used": 0.42},
    )

    post_resp = MagicMock()
    post_resp.ok = True
    post_mock = MagicMock(return_value=post_resp)
    monkeypatch.setattr(solution_service.requests, "post", post_mock)

    perf = MagicMock(return_value=88.0)
    monkeypatch.setattr(solution_service, "compute_performance_percentile", perf)

    upd = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(solution_service, "update_solution_status", upd)

    res = solution_service.process_solution("sid")

    assert res["status"] == "AC"
    assert res["faster_than"] == 88.0
    perf.assert_called_once_with(db, "p1", 0.42)
    post_mock.assert_called_once()
    upd.assert_called_once()
    db.close.assert_called_once()


def test_process_solution_non_AC_sets_faster_than_none(monkeypatch, logger_mock):
    monkeypatch.setattr(solution_service, "logger", logger_mock)
    monkeypatch.setattr(solution_service, "settings", DummySettings)

    db = MagicMock()
    monkeypatch.setattr(solution_service, "SessionLocal", lambda: db)

    sol = MagicMock()
    sol.problem_id = "p1"
    sol.created_by = "u1"
    sol.code = "code"
    sol.language = "python"
    monkeypatch.setattr(solution_service, "get_solution", lambda db, sid: sol)

    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.json.return_value = {"test_cases": [], "time_limit": 1, "memory_limit": 64}
    monkeypatch.setattr(solution_service.requests, "get", lambda url: get_resp)

    monkeypatch.setattr(
        solution_service,
        "run_solution_in_container",
        lambda *a, **k: {"status": "WA", "results": [], "time_used": 0.1},
    )

    perf = MagicMock()
    monkeypatch.setattr(solution_service, "compute_performance_percentile", perf)

    upd = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(solution_service, "update_solution_status", upd)

    res = solution_service.process_solution("sid")
    assert res["faster_than"] is None
    perf.assert_not_called()
    db.close.assert_called_once()


def test_list_solutions_by_problem(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(solution_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock()]

    res = solution_service.list_solutions_by_problem(db_session, "p1")
    assert len(res) == 2
    logger_mock.info.assert_called_once()


def test_list_solutions_by_problem_and_user(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(solution_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [MagicMock()]

    res = solution_service.list_solutions_by_problem_and_user(db_session, "p1", "u1")
    assert len(res) == 1
    logger_mock.info.assert_called_once()


def test_list_contest_solutions_happy_path_with_filters(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(solution_service, "logger", logger_mock)
    monkeypatch.setattr(solution_service, "settings", DummySettings)

    tasks_resp = MagicMock()
    tasks_resp.raise_for_status.return_value = None
    tasks_resp.json.return_value = [{"id": "t1"}, {"id": "t2"}]

    parts_resp = MagicMock()
    parts_resp.raise_for_status.return_value = None
    parts_resp.json.return_value = [{"keycloak_id": "u1"}, {"keycloak_id": "u2"}]

    get_mock = MagicMock(side_effect=[tasks_resp, parts_resp])
    monkeypatch.setattr(solution_service.requests, "get", get_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.filter.return_value = chain
    chain.offset.return_value = chain
    chain.limit.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock(), MagicMock()]

    res = solution_service.list_contest_solutions(
        db_session,
        contest_id="c1",
        owner_id="owner",
        user_id="u1",
        problem_id="t1",
        offset=5,
        limit=3,
    )

    assert len(res) == 3
    assert get_mock.call_count == 2
    chain.offset.assert_called_once_with(5)
    chain.limit.assert_called_once_with(3)
    logger_mock.info.assert_called_once()
