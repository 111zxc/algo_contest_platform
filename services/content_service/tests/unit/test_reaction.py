import pytest
from unittest.mock import MagicMock

import app.services.reaction as reaction_service


class ReactionStub:
    target_id = object()
    target_type = object()
    created_by = object()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_create_reaction_success(db_session, logger_mock, monkeypatch, simple_obj):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    reaction_in = simple_obj(
        user_id="u1",
        target_id="t1",
        target_type="post",
        reaction_type=reaction_service.ReactionType.plus,
    )

    created = MagicMock()
    def fake_reaction_ctor(**kwargs):
        assert kwargs["created_by"] == "u1"
        assert kwargs["target_id"] == "t1"
        assert kwargs["target_type"] == "post"
        assert kwargs["reaction_type"] == reaction_service.ReactionType.plus
        return created

    monkeypatch.setattr(reaction_service, "Reaction", fake_reaction_ctor)

    res = reaction_service.create_reaction(db_session, reaction_in)
    assert res is created
    db_session.add.assert_called_once_with(created)
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created)
    logger_mock.info.assert_called_once()


def test_get_reaction_not_found_logs_warning(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    res = reaction_service.get_reaction(db_session, "rid")
    assert res is None
    logger_mock.warning.assert_called_once()


def test_delete_reaction_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)
    r = MagicMock()
    r.id = "rid"

    reaction_service.delete_reaction(db_session, r)
    db_session.delete.assert_called_once_with(r)
    db_session.commit.assert_called_once()
    logger_mock.info.assert_called_once()


def test_set_reaction_same_reaction_deletes_and_returns_none(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    existing = MagicMock()
    existing.reaction_type = reaction_service.ReactionType.plus

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = existing

    res = reaction_service.set_reaction(
        db_session,
        target_id="t1",
        target_type="post",
        reaction_type=reaction_service.ReactionType.plus,
        user_id="u1",
    )

    assert res is None
    db_session.delete.assert_called_once_with(existing)
    db_session.commit.assert_called_once()


def test_set_reaction_opposite_reaction_replaces(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    existing = MagicMock()
    existing.reaction_type = reaction_service.ReactionType.plus

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = existing

    monkeypatch.setattr(reaction_service, "Reaction", ReactionStub)

    res = reaction_service.set_reaction(
        db_session,
        target_id="t1",
        target_type="post",
        reaction_type=reaction_service.ReactionType.minus,
        user_id="u1",
    )

    assert db_session.delete.call_args_list[0].args[0] is existing
    assert res.created_by == "u1"
    assert res.target_id == "t1"
    assert res.target_type == "post"
    assert res.reaction_type == reaction_service.ReactionType.minus


def test_set_reaction_no_existing_creates_new(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = None

    monkeypatch.setattr(reaction_service, "Reaction", ReactionStub)

    res = reaction_service.set_reaction(
        db_session,
        target_id="t1",
        target_type="post",
        reaction_type=reaction_service.ReactionType.plus,
        user_id="u1",
    )

    assert res.created_by == "u1"
    assert res.target_id == "t1"
    assert res.target_type == "post"
    assert res.reaction_type == reaction_service.ReactionType.plus
    logger_mock.info.assert_called()


def test_list_reactions_for_target_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [MagicMock(), MagicMock()]

    res = reaction_service.list_reactions_for_target(db_session, "t1", "post")
    assert len(res) == 2
    logger_mock.info.assert_called_once()


def test_compute_reaction_balance_counts_plus_minus(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    plus = MagicMock()
    plus.reaction_type = reaction_service.ReactionType.plus
    minus = MagicMock()
    minus.reaction_type = reaction_service.ReactionType.minus
    other = MagicMock()
    other.reaction_type = "whatever"

    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.all.return_value = [plus, minus, plus, other]

    bal = reaction_service.compute_reaction_balance(db_session, "t1", "post")
    assert bal == 1  # +1 -1 +1 +0


def test_get_user_reaction_success(db_session, logger_mock, monkeypatch):
    monkeypatch.setattr(reaction_service, "logger", logger_mock)

    r = MagicMock()
    q = MagicMock()
    chain = MagicMock()
    db_session.query.return_value = q
    q.filter.return_value = chain
    chain.first.return_value = r

    res = reaction_service.get_user_reaction(db_session, "t1", "post", "u1")
    assert res is r
    logger_mock.info.assert_called_once()
