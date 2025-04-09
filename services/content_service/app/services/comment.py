from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.comment import Comment
from app.schemas.comment import CommentCreate


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
