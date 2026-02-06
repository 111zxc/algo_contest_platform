from unittest.mock import MagicMock
import pytest

import app.services.analytics as analytics_service


def test_compute_performance_percentile_no_accepted_returns_100(db_session, logger_mock, monkeypatch):
    q1 = MagicMock()
    chain1 = MagicMock()
    db_session.query.return_value = q1
    q1.filter.return_value = chain1
    chain1.count.return_value = 0

    res = analytics_service.compute_performance_percentile(db_session, "pid", 1.23)
    assert res == 100.0


def test_compute_performance_percentile_computes_ratio(db_session, logger_mock, monkeypatch):
    q_total = MagicMock()
    chain_total = MagicMock()
    q_slow = MagicMock()
    chain_slow = MagicMock()

    db_session.query.side_effect = [q_total, q_slow]

    q_total.filter.return_value = chain_total
    chain_total.count.return_value = 10

    q_slow.filter.return_value = chain_slow
    chain_slow.count.return_value = 3

    res = analytics_service.compute_performance_percentile(db_session, "pid", 2.0)
    assert res == 30.0
