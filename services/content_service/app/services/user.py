from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    user = User(
        keycloak_id=user_in.keycloak_id,
        username=user_in.username,
        email=user_in.email,
        display_name=user_in.display_name,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Succesfully created user {user.username} with id: {user.keycloak_id}")
    return user


def get_user(db: Session, keycloak_id: str) -> User | None:
    result = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if result is None:
        logger.info(f"Couldn't find user with id {keycloak_id}")
    else:
        logger.info(f"Succesfully got user with id {keycloak_id}")
    return result


def update_user(db: Session, user: User, update_data: dict) -> User:
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    logger.info(f"Succesfully updated user {user.username} with id: {user.keycloak_id}")
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
    logger.info(f"Succesfully deleted user {user.username} with id: {user.keycloak_id}")


def get_users(db: Session) -> list[User]:
    logger.info("Succesfully got all users")
    return db.query(User).all()
