from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.models.post import Post
from app.models.reaction import Reaction, ReactionType
from app.models.user import User
from app.schemas.post import PostCreate


def create_post(db: Session, post_in: PostCreate, user_id: str) -> Post:
    """
    Создает и возвращает объект поста, используя данные из переданной схемы

    Args:
        db (Session): объект сессии БД
        post_in (PostCreate): объект с данными для создания поста
        user_id (str): User.keycloak_id пользователя, создавшего пост

    Returns:
        Post - созданный пост
    """
    post = Post(
        problem_id=post_in.problem_id,
        created_by=user_id,
        title=post_in.title,
        content=post_in.content,
        language=post_in.language,
        status=post_in.status,
    )
    try:
        db.add(post)
        db.commit()
        db.refresh(post)
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't create post: {str(e)}")
        raise
    else:
        logger.info(f"Successfully created post with id: {post.id}")
    return post


def get_post(db: Session, post_id: str) -> Post | None:
    """
    Возвращает объект поста по идентификатору или None, если пост не найден

    Args:
        db (Session): объект сессии БД
        post_id (str): идентификатор поста

    Returns:
        Post | None - найденный пост или None, если пост не существует
    """
    try:
        result = (
            db.query(Post)
            .filter(Post.id == post_id)
            .options(joinedload(Post.tags))
            .first()
        )
    except Exception as e:
        logger.error(f"Error getting post with id {post_id}: {str(e)}")
        raise
    else:
        if result is None:
            logger.warning(f"Couldn't get post with id: {post_id}")
        else:
            logger.info(f"Successfully got post with id: {post_id}")
    return result


def update_post(db: Session, post: Post, update_data: dict) -> Post:
    """
    Обновляет запись поста и возвращает обновленный объект поста

    Args:
        db (Session): объект сессии БД
        post (Post): объект поста для обновления
        update_data (dict): словарь с данными для обновления

    Returns:
        Post - обновленный пост
    """
    for key, value in update_data.items():
        setattr(post, key, value)
    try:
        db.commit()
        db.refresh(post)
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't update post with id: {post.id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully updated post with id: {post.id}")
    return post


def delete_post(db: Session, post: Post) -> None:
    """
    Удаляет запись поста

    Args:
        db (Session): объект сессии БД
        post (Post): объект поста для удаления

    Returns:
        None
    """
    try:
        db.delete(post)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Couldn't delete post with id: {post.id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully deleted post with id: {post.id}")


def list_posts(db: Session) -> list[Post]:
    """
    Возвращает список всех постов

    Args:
        db (Session): объект сессии БД

    Returns:
        list[Post] - список постов
    """
    try:
        posts = db.query(Post).options(joinedload(Post.tags)).all()
    except Exception as e:
        logger.error(f"Couldn't get all posts: {str(e)}")
        raise
    else:
        logger.info(f"Successfully got all {len(posts)} posts")
    return posts


def list_posts_by_user(db: Session, keycloak_id: str) -> list[Post]:
    """
    Возвращает список всех постов, созданных указанным пользователем

    Args:
        db (Session): объект сессии БД
        keycloak_id (str): идентификатор пользователя

    Returns:
        list[Post] - список постов, созданных указанным пользователем
    """
    try:
        posts = (
            db.query(Post)
            .options(joinedload(Post.tags))
            .filter(Post.created_by == keycloak_id)
            .all()
        )
    except Exception as e:
        logger.error(f"Couldn't get posts by user {keycloak_id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully got all {len(posts)} posts by user {keycloak_id}")
    return posts


def list_posts_by_problem(db: Session, problem_id: str) -> list[Post]:
    """
    Возвращает список всех постов, связанных с указанной задачей

    Args:
        db (Session): объект сессии БД
        problem_id (str): идентификатор задачи

    Returns:
        list[Post] - список постов, связанных с задачей
    """
    try:
        posts = (
            db.query(Post)
            .options(joinedload(Post.tags))
            .filter(Post.problem_id == problem_id)
            .all()
        )
    except Exception as e:
        logger.error(f"Couldn't get posts by problem {problem_id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully got all {len(posts)} posts by problem {problem_id}")
    return posts


def list_posts_by_tag(db: Session, tag_id: str) -> list[Post]:
    """
    Возвращает список всех постов, содержащих заданный тег

    Args:
        db (Session): объект сессии БД
        tag_id (str): идентификатор тега

    Returns:
        list[Post] - список постов с заданным тегом
    """
    try:
        posts = (
            db.query(Post)
            .options(joinedload(Post.tags))
            .filter(Post.tags.any(id=tag_id))
            .all()
        )
    except Exception as e:
        logger.error(f"Couldn't get posts by tag {tag_id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully got all {len(posts)} posts by tag {tag_id}")
    return posts


def list_enriched_posts_by_problem(
    db: Session,
    problem_id: str,
    offset: int = 0,
    limit: int = 10,
    tag_id: str | None = None,
    sort_by_rating: bool = False,
    sort_order: str = "desc",  # "asc", "desc"
) -> list[Post]:
    """
    Возвращает список постов для указанной задачи problem_id с дополнительными полями author_display_name, ..
    .. reaction_balance; с использованием пагинации, фильтрацией по сложности и тегу; сортировкой по рейтингу

    Args:
        db (Session): сессия базы данных
        problem_id (str): идентификатор данной задачи
        offset (int): смещение для пагинации
        limit (int): количество постов на страницу
        tag_id (Optional[str]): опционально, фильтрует посты, имеющие тег с данным Tag.id
        sort_by_rating (bool): если True, сортирует результаты по рейтингу
        sort_order (str): направление сортировки ("asc", "desc"), по умолчанию "desc".

    Returns:
        List[Post] - список постов к указанной задаче с указанными параметрами
    """
    try:
        reaction_subq = (
            db.query(
                Reaction.target_id.label("post_id"),
                func.sum(
                    case(
                        (Reaction.reaction_type == ReactionType.plus, 1),
                        (Reaction.reaction_type == ReactionType.minus, -1),
                        else_=0,
                    )
                ).label("balance"),
            )
            .filter(Reaction.target_type == "post")
            .group_by(Reaction.target_id)
            .subquery()
        )
    except Exception as e:
        logger.error(f"Couldn't compute reaction subquery: {str(e)}")
        raise

    try:
        query = (
            db.query(Post, User.display_name, reaction_subq.c.balance)
            .join(User, Post.created_by == User.keycloak_id)
            .outerjoin(reaction_subq, Post.id == reaction_subq.c.post_id)
            .filter(Post.problem_id == problem_id)
        )
        if tag_id:
            query = query.filter(Post.tags.any(id=tag_id))
        if sort_by_rating:
            if sort_order.lower() == "asc":
                query = query.order_by(func.coalesce(reaction_subq.c.balance, 0).asc())
            else:
                query = query.order_by(func.coalesce(reaction_subq.c.balance, 0).desc())
        query = query.offset(offset).limit(limit)
        results = query.all()
    except Exception as e:
        logger.error(f"Couldn't list enriched posts: {str(e)}")
        raise

    enriched = []
    for post, display_name, balance in results:
        setattr(post, "author_display_name", display_name)
        setattr(post, "reaction_balance", balance if balance is not None else 0)
        enriched.append(post)
    logger.info(
        f"Successfully got {len(enriched)} enriched posts for problem {problem_id}"
    )
    return enriched
