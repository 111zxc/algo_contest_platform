from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.contest import Contest
from app.models.problem import Problem
from app.models.user import User
from app.schemas.contest import ContestCreate
from app.services.user import get_user, get_user_by_username


def create_contest(db: Session, data: ContestCreate, owner_id: str) -> Contest:
    contest = Contest(
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        created_by=owner_id,
    )
    try:
        db.add(contest)
        db.commit()
        db.refresh(contest)
    except Exception:
        db.rollback()
        logger.exception("contest_create_failed",
                         extra={'owner_id': owner_id})
        raise
    logger.debug("contest_create",
                 extra={'owner_id': owner_id})
    return contest


def get_contest(db: Session, contest_id: str) -> Contest | None:
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        logger.warning("contest_get_notfound",
                       extra={'contest_id': contest_id})
    else:
        logger.debug("contest_get",
                     extra={'contest_id': contest_id})
    return contest


def update_contest(db: Session, contest: Contest, data: dict) -> Contest:
    for k, v in data.items():
        setattr(contest, k, v)
    try:
        db.commit()
        db.refresh(contest)
    except Exception:
        db.rollback()
        logger.exception("contest_update_failed",
                         extra={'contest_id': str(contest.id), 'owner_id': str(contest.created_by)})
        raise
    logger.debug("contest_update",
                 extra={'contest_id': str(contest.id)})
    return contest


def delete_contest(db: Session, contest: Contest) -> None:
    try:
        db.delete(contest)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("contest_delete_failed",
                         extra={'contest_id': str(contest.id), 'owner_id': str(contest.created_by)})
        raise
    logger.debug("contest_delete",
                 extra={'contest_id': str(contest.id)})


def list_public_contests(
    db: Session, offset: int = 0, limit: int = 10
) -> list[Contest]:
    try:
        result = (
            db.query(Contest)
            .filter(Contest.is_public)
            .order_by(Contest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    except Exception:
        logger.exception("contest_publiclist_failed",
                         extra={'offset': offset, 'limit': limit})
        raise
    else:
        logger.debug("contest_publiclist",
                     extra={'length': len(result)})
    return result


def list_owner_contests(db: Session, owner_id: str) -> list[Contest]:
    result = (
        db.query(Contest)
        .filter(Contest.created_by == owner_id)
        .order_by(Contest.created_at.desc())
        .all()
    )
    logger.debug('contest_ownerlist',
                 extra={'length': len(result)})
    return result


def join_public_contest(db: Session, contest_id: str, user_id: str):
    contest = get_contest(db, contest_id)

    if not contest.is_public:
        logger.error("contest_join_failed",
                     extra={'user_id': user_id, 'contest_id': contest_id})
        return

    if any(user.keycloak_id == user_id for user in contest.participants):
        logger.error("contest_join_failed",
                     extra={'detail': 'user already joined', 'user_id': user_id, 'contest_id': contest_id})
        return
    user = get_user(db, user_id)
    contest.participants.append(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("contest_join_failed",
                         extra={'user_id': user_id, 'contest_id': contest_id})
        raise
    logger.debug("contest_join",
                extra={'user_id': user_id, 'contest_id': contest_id})


def add_user_to_contest_by_username(db: Session, contest_id: str, target_username: str):
    contest = get_contest(db, contest_id)
    user = get_user_by_username(db, target_username)
    target_user_id = user.keycloak_id

    if any(user.username == target_user_id for user in contest.participants):
        logger.error('contest_addusername_failed',
                     extra={'detail': 'user already in contest', 'target_id': target_username, 'contest_id': contest_id})
        return
    contest.participants.append(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("contest_addusername_failed",
                         extra={'target_username': target_username, 'contest_id': contest_id})
        raise
    logger.debug("contest_addusername",
                 extra={'target_username': target_username, 'contest_id': contest_id})


def list_contest_participants(db: Session, contest_id: str) -> list[User]:
    contest = get_contest(db, contest_id)
    logger.debug('contest_listparticipants',
                 extra={'length': len(contest.participants)})
    return contest.participants


def list_contest_tasks(db: Session, contest_id: str) -> list[Problem]:
    try:
        problems = db.query(Problem).filter(Problem.contest_id == contest_id).all()
    except Exception:
        logger.exception("contest_listtasks_failed",
                         extra={'contest_id': contest_id})
        raise
    else:
        logger.debug("contest_listtasks",
                     extra={'contest_id': contest_id, 'length': len(problems)})
    return problems


def list_user_contests(db: Session, user_id: str) -> list[Contest]:
    try:
        user = get_user(db, user_id)
    except Exception:
        logger.exception("contest_listuser_failed",
                         extra={'user_id': user_id})
        raise
    else:
        logger.debug("contest_listuser",
                     extra={"user_id": user_id, 'length': len(user.contests_joined)})
    return user.contests_joined
