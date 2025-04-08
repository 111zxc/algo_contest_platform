from sqlalchemy.orm import Session, joinedload

from app.models.post import Post
from app.schemas.post import PostCreate


def create_post(db: Session, post_in: PostCreate, user_id: str) -> Post:
    post = Post(
        problem_id=post_in.problem_id,
        created_by=user_id,
        content=post_in.content,
        language=post_in.language,
        status=post_in.status,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: str) -> Post | None:
    return (
        db.query(Post).filter(Post.id == post_id).options(joinedload(Post.tags)).first()
    )


def update_post(db: Session, post: Post, update_data: dict) -> Post:
    for key, value in update_data.items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def list_posts(db: Session) -> list[Post]:
    return db.query(Post).options(joinedload(Post.tags)).all()


def list_posts_by_user(db: Session, keycloak_id: str) -> list[Post]:
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.created_by == keycloak_id)
        .all()
    )


def list_posts_by_problem(db: Session, problem_id: str) -> list[Post]:
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.problem_id == problem_id)
        .all()
    )


def list_posts_by_tag(db: Session, tag_id: str) -> list[Post]:
    return (
        db.query(Post)
        .options(joinedload(Post.tags))
        .filter(Post.tags.any(id=tag_id))
        .all()
    )
