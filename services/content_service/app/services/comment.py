from sqlalchemy.orm import Session

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
    return comment


def get_comment(db: Session, comment_id: str) -> Comment | None:
    return db.query(Comment).filter(Comment.id == comment_id).first()


def update_comment(db: Session, comment: Comment, update_data: dict) -> Comment:
    for key, value in update_data.items():
        setattr(comment, key, value)
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    db.delete(comment)
    db.commit()


def list_comments_by_post(db: Session, post_id: str) -> list[Comment]:
    return db.query(Comment).filter(Comment.post_id == post_id).all()


def list_comments_by_user(db: Session, keycloak_id: str) -> list[Comment]:
    return db.query(Comment).filter(Comment.created_by == keycloak_id).all()
