from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.tag import Tag
from app.schemas.tag import TagCreate


def create_tag(db: Session, tag_in: TagCreate) -> Tag:
    tag = Tag(
        name=tag_in.name,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    logger.info(f"Succesfully created tag {tag.name}")
    return tag


def get_tag(db: Session, tag_id: str) -> Tag | None:
    result = db.query(Tag).filter(Tag.id == tag_id).first()
    if result is None:
        logger.info("Couldn't get tag with id: {tag_id}")
    else:
        logger.info(f"Succesfully got tag with id: {tag_id}")
    return result


def update_tag(db: Session, tag: Tag, update_data: dict) -> Tag:
    for key, value in update_data.items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    logger.info(f"Succesfully updated tag {tag.name} with id {tag.id}")
    return tag


def delete_tag(db: Session, tag: Tag) -> None:
    db.delete(tag)
    db.commit()
    logger.info(f"Succesfully deleted tag {tag.name}")


def get_tags(db: Session) -> list[Tag]:
    logger.info("Succesfully got all tags")
    return db.query(Tag).all()
