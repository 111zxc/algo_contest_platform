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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't create blog post with title {data.title}: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully created blog post {data.title}")
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
    except Exception as e:
        logger.error(f"Error getting blog post by id {post_id}: {str(e)}")
        raise

    if result is None:
        logger.warning(f"Couldn't get blog post by id {post_id}")
    else:
        logger.info(f"Succesfully got blog post {post_id}")
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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't update blog post {post.id}: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully updated blog post {post.id}")
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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't delete blog post {post.id}: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully deleted blog post {post.id}")
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
    except Exception as e:
        logger.error(f"Couldn't list blog posts: {str(e)}")
        raise
    else:
        logger.info(f"Succesfully got {len(result)} blog posts")
    return result
