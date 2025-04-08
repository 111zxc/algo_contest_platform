from sqlalchemy.orm import Session

from app.models.tag import Tag
from app.schemas.tag import TagCreate


def create_tag(db: Session, tag_in: TagCreate) -> Tag:
    tag = Tag(
        name=tag_in.name,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def get_tag(db: Session, tag_id: str) -> Tag | None:
    return db.query(Tag).filter(Tag.id == tag_id).first()


def update_tag(db: Session, tag: Tag, update_data: dict) -> Tag:
    for key, value in update_data.items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    return tag


def delete_tag(db: Session, tag: Tag) -> None:
    db.delete(tag)
    db.commit()


def get_tags(db: Session) -> list[Tag]:
    return db.query(Tag).all()
