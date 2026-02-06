from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.services.reaction import compute_reaction_balance


def create_comment(db: Session, comment_in: CommentCreate, user_id: str) -> Comment:
    """
    Создает и возвращает запись комментария, используя данные из данного CommentCreate

    Args:
        db (Session): объект сессии БД
        comment_in (CommentCreate): объект с данными для создания комментария
        user_id (str): идентификатор пользователя, создавшего комментарий

    Returns:
        Comment - созданный комментарий
    """
    comment = Comment(
        post_id=comment_in.post_id,
        created_by=user_id,
        content=comment_in.content,
        parent_comment_id=comment_in.parent_comment_id,
    )
    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)
    except Exception:
        db.rollback()
        logger.exception("comment_create_failed")
        raise
    else:
        logger.debug(
            "comment_create",
            extra={'comment_id': str(comment.id), "post_id": str(comment.post_id), 'created_by': str(comment.created_by)}
        )
    return comment


def get_comment(db: Session, comment_id: str) -> Comment | None:
    """
    Возвращает объект комментария по идентификатору или None, если комментарий не найден

    Args:
        db (Session): объект сессии БД
        comment_id (str): идентификатор комментария

    Returns:
        Comment | None - найденный комментарий или None, если комментарий не существует
    """
    try:
        result = db.query(Comment).filter(Comment.id == comment_id).first()
    except Exception:
        logger.error("comment_get_failed",
                     extra={'comment_id': comment_id})
        raise
    else:
        if result is None:
            logger.warning("comment_notfound",
                           extra={'comment_id': comment_id})
        else:
            logger.debug("comment_get",
                        extra={'comment_id': comment_id})
    return result


def update_comment(db: Session, comment: Comment, update_data: dict) -> Comment:
    """
    Обновляет данные комментария и возвращает обновленный объект комментария

    Args:
        db (Session): объект сессии БД
        comment (Comment): объект комментария, который требуется обновить
        update_data (dict): словарь с данными для обновления

    Returns:
        Comment - обновленный комментарий
    """
    for key, value in update_data.items():
        setattr(comment, key, value)
    try:
        db.commit()
        db.refresh(comment)
    except Exception:
        db.rollback()
        logger.exception("comment_update_failed",
                         extra={'comment_id': str(comment.id)})
        raise
    else:
        logger.debug("comment_update",
                     extra={'comment_id': str(comment.id), 'created_by': str(comment.created_by)})
    return comment


def delete_comment(db: Session, comment: Comment) -> None:
    """
    Удаляет запись комментария

    Args:
        db (Session): объект сессии БД
        comment (Comment): объект комментария для удаления

    Returns:
        None
    """
    try:
        db.delete(comment)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("comment_delete_failed",
                         extra={'comment_id': str(comment.id), 'created_by': str(comment.created_by)})
        raise
    else:
        logger.debug("comment_delete",
                     extra={'comment_id': str(comment.id), 'created_by': str(comment.created_by)})


def list_comments_by_post(db: Session, post_id: str) -> list[Comment]:
    """
    Возвращает список комментариев для заданного поста

    Args:
        db (Session): объект сессии БД
        post_id (str): идентификатор поста

    Returns:
        list[Comment] - список комментариев для поста
    """
    try:
        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    except Exception:
        logger.exception("comment_list_failed",
                         extra={'post_id': post_id})
        raise
    else:
        logger.debug("comment_list",
                     extra={'post_id': post_id, 'length': len(comments)})
    return comments


def list_comments_by_user(db: Session, keycloak_id: str) -> list[Comment]:
    """
    Возвращает список комментариев, созданных указанным пользователем

    Args:
        db (Session): объект сессии БД
        keycloak_id (str): идентификатор пользователя (Keycloak ID)

    Returns:
        list[Comment] - список комментариев, созданных пользователем
    """
    try:
        comments = db.query(Comment).filter(Comment.created_by == keycloak_id).all()
    except Exception:
        logger.exception("comment_list_failed",
                         extra={'user_id': keycloak_id})
        raise
    else:
        logger.debug("comment_list",
                     extra={'user_id': keycloak_id, 'length': len(comments)})
    return comments


def list_enriched_comments_by_post(
    db: Session, post_id: str, offset: int = 0, limit: int = 10
) -> list[Comment]:
    """
    Возвращает список комментариев для указанного поста post_id с дополнительными полями author_display_name, ..
    .. reaction_balance; с использованием пагинации

    Args:
        db (Session): сессия базы данных
        post_id (str): идентификатор данного поста
        offset (int): смещение для пагинации
        limit (int): количество комментариев на страницу

    Returns:
        List[Comment] - список комментариев к указанной задаче
    """
    try:
        results = (
            db.query(Comment, User.display_name)
            .join(User, Comment.created_by == User.keycloak_id)
            .filter(Comment.post_id == post_id)
            .offset(offset)
            .limit(limit)
            .all()
        )
    except Exception:
        logger.exception("comment_listenriched_failed",
                         extra={'post_id': post_id, 'offset': offset, 'limit': limit})
        raise

    enriched = []
    for comment, display_name in results:
        setattr(comment, "author_display_name", display_name)
        balance = compute_reaction_balance(db, str(comment.id), "comment")
        setattr(comment, "reaction_balance", balance)
        enriched.append(comment)
    logger.debug("comment_listenriched",
                 extra={'post_id': post_id, 'offset': offset, 'limit': limit, 'length': len(enriched)})
    return enriched