from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.models.post import Post
from app.schemas.post import PostCreate
from app.models.user import User


def create_post(db: Session, post_in: PostCreate, user_id: str) -> Post:
    post = Post(
        problem_id=post_in.problem_id,
        created_by=user_id,
        title=post_in.title,
        content=post_in.content,
        language=post_in.language,
        status=post_in.status,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    logger.info(f"Created post with id: {post.id}")
    return post


def get_post(db: Session, post_id: str) -> Post | None:
    result = (
        db.query(Post).filter(Post.id == post_id).options(joinedload(Post.tags)).first()
    )
    if result is None:
        logger.info(f"Couldn't get post with {post_id}")
    else:
        logger.info(f"Succesfully got post with id: {post_id}")
    return result


def update_post(db: Session, post: Post, update_data: dict) -> Post:
    for key, value in update_data.items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    logger.info(f"Succesfully updated post with {post.id}")
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    logger.info(f"Succesfully deleted post with id: {post.id}")
    db.commit()


def list_posts(db: Session) -> list[Post]:
    logger.info("Succesfully got all posts")
    return db.query(Post).options(joinedload(Post.tags)).all()


def list_posts_by_user(db: Session, keycloak_id: str) -> list[Post]:
    logger.info(f"Succesfully got all posts by user {keycloak_id}")
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.created_by == keycloak_id)
        .all()
    )


def list_posts_by_problem(db: Session, problem_id: str) -> list[Post]:
    logger.info(f"Succesfully got all posts by problem {problem_id}")
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.problem_id == problem_id)
        .all()
    )


def list_posts_by_tag(db: Session, tag_id: str) -> list[Post]:
    logger.info(f"Succesfully got all posts by tag {tag_id}")
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.tags.any(id=tag_id))
        .all()
    )

def list_enriched_posts_by_problem(db: Session, problem_id: str, offset: int = 0, limit: int = 10) -> list[Post]:
    """
    Возвращает список постов для задачи problem_id с дополнением поля author_display_name,
    используя пагинацию (offset и limit).

    Args:
        db (Session): Сессия для работы с БД.
        problem_id (str): Идентификатор задачи.
        offset (int): Смещение (начинается с 0).
        limit (int): Максимальное количество записей.

    Returns:
        List[Post]: Список постов, каждому из которых добавлено свойство author_display_name.
    """
    # Выполняем join Post и User по полю Post.user_id == User.keycloak_id
    results = (
        db.query(Post, User.display_name)
          .join(User, Post.created_by == User.keycloak_id)
          .filter(Post.problem_id == problem_id)
          .offset(offset)
          .limit(limit)
          .all()
    )
    enriched = []
    for post, display_name in results:
        setattr(post, "author_display_name", display_name)
        enriched.append(post)
    return enriched