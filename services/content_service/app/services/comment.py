from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.comment import Comment
from app.schemas.comment import CommentCreate
from app.models.user import User


def create_comment(db: Session, comment_in: CommentCreate, user_id: str) -> Comment:
    comment = Comment(
        post_id=comment_in.post_id,
        created_by=user_id,
        content=comment_in.content,
        parent_comment_id=comment_in.parent_comment_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    logger.info(f"Succesfully created comment {comment.id} from {comment.created_by} to {comment.post_id}")
    return comment


def get_comment(db: Session, comment_id: str) -> Comment | None:
    result = db.query(Comment).filter(Comment.id == comment_id).first()
    logger.info(f"Succesfully got comment {comment_id}")
    return result


def update_comment(db: Session, comment: Comment, update_data: dict) -> Comment:
    for key, value in update_data.items():
        setattr(comment, key, value)
    db.commit()
    db.refresh(comment)
    logger.info(f"Succesfully updated comment {comment.id}")
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    logger.info(f"Succesfully deleted comment {comment.id}")
    db.commit()


def list_comments_by_post(db: Session, post_id: str) -> list[Comment]:
    logger.info(f"Succesfully got all comments to post {post_id}")
    return db.query(Comment).filter(Comment.post_id == post_id).all()


def list_comments_by_user(db: Session, keycloak_id: str) -> list[Comment]:
    logger.info(f"Succesfully got all comments to user {keycloak_id}")
    return db.query(Comment).filter(Comment.created_by == keycloak_id).all()


def list_enriched_comments_by_post(db: Session, post_id: str, offset: int = 0, limit: int = 10) -> list[Comment]:
    """
    Возвращает список комментариев для поста post_id, обогащенных полем author_display_name.
    Пагинация задается через offset и limit.
    
    Args:
        db (Session): Сессия для работы с БД.
        post_id (str): Идентификатор поста.
        offset (int): Смещение для пагинации.
        limit (int): Максимальное число записей.
    
    Returns:
        List[Comment]: Список комментариев, каждый с добавленным полем author_display_name.
    """
    results = (
        db.query(Comment, User.display_name)
          .join(User, Comment.created_by == User.keycloak_id)
          .filter(Comment.post_id == post_id)
          .offset(offset)
          .limit(limit)
          .all()
    )
    enriched = []
    for comment, display_name in results:
        setattr(comment, "author_display_name", display_name)
        enriched.append(comment)
    return enriched