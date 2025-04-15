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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't create comment: {str(e)}")
        raise
    else:
        logger.info(
            f"Successfully created comment {comment.id} from {comment.created_by} to {comment.post_id}"
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
    except Exception as e:
        logger.error(f"Error getting comment with id {comment_id}: {str(e)}")
        raise
    else:
        if result is None:
            logger.warning(f"Couldn't get comment {comment_id}")
        else:
            logger.info(f"Successfully got comment {comment_id}")
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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't update comment {comment.id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully updated comment {comment.id}")
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
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't delete comment {comment.id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully deleted comment {comment.id}")


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
    except Exception as e:
        logger.error(f"Couldn't get comments for post {post_id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully got all {len(comments)} comments for post {post_id}")
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
    except Exception as e:
        logger.error(f"Couldn't get comments for user {keycloak_id}: {str(e)}")
        raise
    else:
        logger.info(
            f"Successfully got all {len(comments)} comments for user {keycloak_id}"
        )
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
    except Exception as e:
        logger.error(f"Couldn't get enriched comments for post {post_id}: {str(e)}")
        raise

    enriched = []
    for comment, display_name in results:
        setattr(comment, "author_display_name", display_name)
        balance = compute_reaction_balance(db, str(comment.id), "comment")
        setattr(comment, "reaction_balance", balance)
        enriched.append(comment)
    logger.info(
        f"Successfully got {len(enriched)} enriched comments for post {post_id}"
    )
    return enriched
