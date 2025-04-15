from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.tag import Tag
from app.schemas.tag import TagCreate


def create_tag(db: Session, tag_in: TagCreate) -> Tag:
    """
    Создает и возвращает объект тега, используя переданные данные.

    Args:
        db (Session): объект сессии БД
        tag_in (TagCreate): объект с данными для создания тега

    Returns:
        Tag - созданный тег
    """
    tag = Tag(
        name=tag_in.name,
    )
    try:
        db.add(tag)
        db.commit()
        db.refresh(tag)
    except Exception as e:
        logger.error(f"Couldn't create tag {tag.name}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully created tag {tag.name}")
    return tag


def get_tag(db: Session, tag_id: str) -> Tag | None:
    """
    Возвращает объект тега по идентификатору или None, если тег не найден.

    Args:
        db (Session): объект сессии БД
        tag_id (str): идентификатор тега

    Returns:
        Tag | None - найденный тег или None, если тег не найден
    """
    result = db.query(Tag).filter(Tag.id == tag_id).first()
    if result is None:
        logger.warning(f"Couldn't get tag with id: {tag_id}")
    else:
        logger.info(f"Succesfully got tag with id: {tag_id}")
    return result


def update_tag(db: Session, tag: Tag, update_data: dict) -> Tag:
    """
    Обновляет данные тега и возвращает обновленный объект.

    Args:
        db (Session): объект сессии БД
        tag (Tag): объект тега, который требуется обновить
        update_data (dict): словарь с данными для обновления

    Returns:
        Tag - обновленный тег
    """
    for key, value in update_data.items():
        setattr(tag, key, value)
    try:
        db.commit()
        db.refresh(tag)
    except Exception as e:
        logger.error(f"Couldn't update tag {tag.name}: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully updated tag {tag.name} with id {tag.id}")
    return tag


def delete_tag(db: Session, tag: Tag) -> None:
    """
    Удаляет запись тега из бд

    Args:
        db (Session): объект сессии БД
        tag (Tag): объект тега для удаления

    Returns:
        None - функция ничего не возвращает
    """
    try:
        db.delete(tag)
        db.commit()
    except Exception as e:
        logger.error(f"Couldn't delete tag {tag.name}: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully deleted tag {tag.name}")


def get_tags(db: Session) -> list[Tag]:
    """
    Возвращает список всех тегов

    Args:
        db (Session): объект сессии БД

    Returns:
        list[Tag] - список тегов
    """
    try:
        tags = db.query(Tag).all()
    except Exception as e:
        logger.error(f"Couldn't get all tags: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully got all {len(tags)} tags")
    return tags
