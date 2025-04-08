from sqlalchemy.orm import Session

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
    return user


def get_user(db: Session, keycloak_id: str) -> User | None:
    return db.query(User).filter(User.keycloak_id == keycloak_id).first()


def update_user(db: Session, user: User, update_data: dict) -> User:
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def get_users(db: Session) -> list[User]:
    return db.query(User).all()
