from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.comment import Comment
from app.models.post import Post
from app.models.problem import Problem
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.reaction import compute_reaction_balance


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Создает запись нового пользователя

    Args:
        db (Session): объект сессии БД,
        user_in (UserCreate): схема данных создания пользователя

    Returns:
        User: orm объект созданного пользователя
    """

    user = User(
        keycloak_id=user_in.keycloak_id,
        username=user_in.username,
        email=user_in.email,
        display_name=user_in.display_name,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        logger.error(f"Couldn't save newly created user {user.username}: {str(e)}")
        raise
    else:
        logger.info(
            f"Successfully created user {user.username} with id: {user.keycloak_id}"
        )
    return user


def get_user(db: Session, keycloak_id: str) -> User | None:
    """
    Возвращает пользователя по его keycloak_id или 404, если пользователя ..
    .. с таким id не существует

    Args:
        db (Session): объект сессии БД,
        keycloak_id (str): User.keycloak_id,

    Returns:
        User | None
    """
    result = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if result is None:
        logger.warning(f"Couldn't find user with id {keycloak_id}")
    else:
        logger.info(f"Successfully got user with id {keycloak_id}")
    return result


def update_user(db: Session, user: User, update_data: dict) -> User:
    """
    Обновляет указанные в update_data поля данного пользователя user

    Args:
        db (Session): объект сессии БД,
        update_data (dict): User."field": new_value

    Returns:
        User - объект обновленного пользователя
    """
    for field, value in update_data.items():
        setattr(user, field, value)
    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        logger.error(
            f"Couldn't save updated user {user.username} with id {user.keycloak_id}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Succesfully updated user {user.username} with id: {user.keycloak_id}"
        )
    return user


def delete_user(db: Session, user: User) -> None:
    """
    Удаляет запись указанного пользователя user

    Args:
        db (Session): объект сессии БД,
        user (User): объект пользователя

    Returns:
        None
    """
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        logger.error(
            f"Couldn't delete user {user.keycloak_id} {user.username}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Succesfully deleted user {user.username} with id: {user.keycloak_id}"
        )


def get_users(db: Session) -> list[User]:
    """
    Возвращает список всех пользователей

    Args:
        db (Session): объект сессии БД

    Returns:
        list[User] - список всех пользователей
    """
    try:
        users = db.query(User).all()
    except Exception as e:
        logger.error(f"Couldn't get all users: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully got all {len(users)} users")
    return db.query(User).all()


def compute_user_rating(db: Session, keycloak_id: str) -> int:
    """
    Вычисляет и возвращает баланс рейтинга пользователя, основанный на реакциях на ..
    .. задачи, посты, комментарии его авторства.

    Args:
        db (Session): объект сессии БД
        keycloak_id (str): User.keycloak_id нужного пользователя

    Returns:
        int - баланс рейтинга данного пользователя
    """
    post_balance = sum(
        compute_reaction_balance(db, str(post.id), "post")
        for post in db.query(Post).filter(Post.created_by == keycloak_id).all()
    )
    problem_balance = sum(
        compute_reaction_balance(db, str(problem.id), "problem")
        for problem in db.query(Problem).filter(Problem.created_by == keycloak_id).all()
    )
    comment_balance = sum(
        compute_reaction_balance(db, str(comment.id), "comment")
        for comment in db.query(Comment).filter(Comment.created_by == keycloak_id).all()
    )

    total_rating = post_balance + problem_balance + comment_balance
    logger.info(f"Computed rating for user {keycloak_id}: {total_rating}")
    return total_rating
