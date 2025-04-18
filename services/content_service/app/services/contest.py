from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.contest import Contest
from app.models.problem import Problem
from app.models.user import User
from app.schemas.contest import ContestCreate
from app.services.user import get_user


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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't create contest {data.name}: {e}")
        raise
    logger.info(f"Successfully created contest {contest.id}")
    return contest


def get_contest(db: Session, contest_id: str) -> Contest | None:
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        logger.warning(f"get_contest[{contest_id}] not found")
    else:
        logger.info(f"Successfully got contest {contest_id}")
    return contest


def update_contest(db: Session, contest: Contest, data: dict) -> Contest:
    for k, v in data.items():
        setattr(contest, k, v)
    try:
        db.commit()
        db.refresh(contest)
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't update contest {contest.id}: {e}")
        raise
    logger.info(f"Successfully updated contest {contest.id}")
    return contest


def delete_contest(db: Session, contest: Contest) -> None:
    try:
        db.delete(contest)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't delete contest {contest.id}: {e}")
        raise
    logger.info(f"Successfully deleted contest {contest.id}")


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
    except Exception as e:
        logger.error(f"Couldn't get contests: {e}")
        raise
    else:
        logger.info(f"Succesfully got {len(result)} public contests")
    return result


def list_owner_contests(db: Session, owner_id: str) -> list[Contest]:
    return (
        db.query(Contest)
        .filter(Contest.created_by == owner_id)
        .order_by(Contest.created_at.desc())
        .all()
    )


def join_public_contest(db: Session, contest_id: str, user_id: str):
    contest = get_contest(db, contest_id)

    if not contest.is_public:
        logger.error(f"{user_id} couldn't join private contest {contest_id}")
        return

    if any(user.keycloak_id == user_id for user in contest.participants):
        return
    user = get_user(db, user_id)
    contest.participants.append(user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"{user_id} couldn't join public contest {contest_id}: {e}")
        raise
    logger.info(f"User {user_id} succesfully joined public contest {contest_id}")


def add_user_to_contest(db: Session, contest_id: str, target_user_id: str):
    contest = get_contest(db, contest_id)
    user = get_user(db, target_user_id)

    if any(user.keycloak_id == target_user_id for user in contest.participants):
        return
    contest.participants.append(user)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't add user {target_user_id} to contest {contest_id}: {e}")
        raise
    logger.info(f"Successfully added user {target_user_id} to contest {contest_id}")


def list_contest_participants(db: Session, contest_id: str) -> list[User]:
    contest = get_contest(db, contest_id)
    return contest.participants


def list_contest_tasks(db: Session, contest_id: str) -> list[Problem]:
    try:
        problems = db.query(Problem).filter(Problem.contest_id == contest_id).all()
    except Exception as e:
        logger.error(f"Couldn't get problems for contest {contest_id}: {e}")
        raise
    else:
        logger.info(
            f"Successfully got all {len(problems)} problems for contest {contest_id}"
        )
    return problems


def list_user_contests(db: Session, user_id: str) -> list[Contest]:
    try:
        user = get_user(db, user_id)
    except Exception as e:
        logger.error(f"Couldn't get user {user_id} contests: {e}")
        raise
    else:
        logger.info(
            f"Successfully got all {len(user.contests_joined)} contests joined for user {user_id}"
        )
    return user.contests_joined
