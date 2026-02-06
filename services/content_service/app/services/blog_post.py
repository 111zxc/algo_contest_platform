from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.blog_post import BlogPost
from app.schemas.blog_post import BlogPostCreate


def create_blog_post(db: Session, data: BlogPostCreate) -> BlogPost:
    """
    Создает новую запись в таблице blog_posts

    Args:
        db (Session): объект сессии БД
        data (BlogPostCreate): данные для создания нового блог поста

    Returns:
        BlogPost - созданный пост
    """
    post = BlogPost(title=data.title, description=data.description)
    try:
        db.add(post)
        db.commit()
        db.refresh(post)
    except Exception:
        db.rollback()
        logger.exception("blogpost_create_failed",
                         extra={"title": data.title})
        raise
    else:
        logger.debug("blogpost_created",
                    extra={"title": data.title})
    return post


def get_blog_post(db: Session, post_id: str) -> BlogPost | None:
    """
    Возвращает BlogPost по его UUID или None

    Args:
        db (Session): объект сессии БД
        post_id (str): идентификатор блог поста

    Returns:
        BlogPost | None - найденный блог или None, если блог не существует
    """
    try:
        result = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    except Exception:
        logger.exception("blogpost_get_failed",
                         extra={"blogpost_id": str(post_id)})
        raise

    if result is None:
        logger.warning("blogpost_notfound",
                       extra={"blogpost_id": str(post_id)})
    else:
        logger.debug("blogpost_get",
                    extra={"blogpost_id": str(post_id)})
    return result


def update_blog_post(db: Session, post: BlogPost, data: dict) -> BlogPost:
    """
    Обновляет title/description у переданного экземпляра post

    Args:
        db (Session): объект сессии БД
        post (BlogPost): объект поста в блоге
        data (dict): данные для обновления у поста

    Returns:
        BlogPost - обновленный объект BlogPost
    """
    for field, value in data.items():
        setattr(post, field, value)
    try:
        db.commit()
        db.refresh(post)
    except Exception:
        db.rollback()
        logger.exception("blogpost_update_failed",
                         extra={"blogpost_id": str(post.id)})
        raise
    else:
        logger.debug("blogpost_update",
                    extra={'blogpost_id': str(post.id)})
    return post


def delete_blog_post(db: Session, post: BlogPost) -> None:
    """
    Удаляет переданный экземпляр post

    Args:
        db (Session): объект сессии БД
        post (BlogPost): объект поста

    Returns:
        None
    """
    try:
        db.delete(post)
    except Exception:
        db.rollback()
        logger.exception('blogpost_delete_failed',
                         extra={'blogpost_id': {post.id}})
        raise
    else:
        logger.debug("blogpost_delete",
                     extra={'blogpost_title': post.title})
    db.commit()


def list_blog_posts(db: Session, offset: int = 0, limit: int = 10) -> list[BlogPost]:
    """
    Возвращает страницы блог‑постов с `offset` и `limit`

    Args:
        db (Session): объект сессии БД
        offset (int): отступ от начала
        limit (int): максимальное количество постов в результате

    Returns:
        list[BlogPost] - список найденных постов с указанными параметрами
    """
    try:
        result = (
            db.query(BlogPost)
            .order_by(BlogPost.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    except Exception:
        logger.exception("blogpost_list_failed")
        raise
    else:
        logger.debug("blogpost_list",
                     extra={'length':len(result)})
    return result
