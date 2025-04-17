from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user
from app.core.database import get_db
from app.schemas.blog_post import BlogPostCreate, BlogPostRead
from app.services.blog_post import (
    create_blog_post,
    delete_blog_post,
    get_blog_post,
    list_blog_posts,
    update_blog_post,
)

router = APIRouter(prefix="/blogposts", tags=["blogposts"])


def get_blogpost_or_404(post_id: str, db: Session = Depends(get_db)):
    """
    Вспомогательная функция
    """
    blog_post = get_blog_post(db, post_id)
    if not blog_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост блога не найден"
        )
    return blog_post


@router.post(
    "/",
    response_model=BlogPostRead,
    status_code=status.HTTP_201_CREATED,
)
@authorize(required_role="admin")
def create_blog_post_endpoint(
    data: BlogPostCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Создает новый BlogPost

    Args:
        data (BlogPostCreate): данные для создания поста
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        BlogPostRead - созданный пост
    """
    return create_blog_post(db, data)


@router.get(
    "/",
    response_model=list[BlogPostRead],
)
def list_blog_posts_endpoint(
    offset: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(10, ge=1, description="Размер страницы"),
    db: Session = Depends(get_db),
):
    """
    Возвращает список блог постов (BlogPostRead)
    Пагинация реализована через параметры offset и limit

    Args:
        offset (int): смещение для выборки (по умолчанию 0)
        limit (int): максимальное число постов на страницу (по умолчанию 10)
        db (Session): сессия для работы с базой данных

    Returns:
        List[BlogPostRead] - список постов
    """
    return list_blog_posts(db, offset, limit)


@router.get(
    "/{post_id}",
    response_model=BlogPostRead,
)
def read_blog_post_endpoint(
    post_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Возвращает блог пост по его идентификатору

    Args:
        post_id (UUID): идентификатор блог поста
        db (Session): объект сессии БД

    Returns:
        BlogPost - найденный пост

    Raises:
        HTTPException 404 - если пост не найден
    """
    return get_blogpost_or_404(post_id, db)


@router.put(
    "/{post_id}",
    response_model=BlogPostRead,
)
@authorize(required_role="admin")
def update_blog_post_endpoint(
    post_id: UUID,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет данные комментария

    Args:
        post_id (UUID): идентификатор поста для обновления
        update_data (dict): данные для обновления
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        BlogPosterad - обновленный пост

    Raises:
        HTTPException 404 - если пост не найден
        HTTPException 403 - если недостаточно прав для обновления
    """
    post = get_blogpost_or_404(post_id, db)
    return update_blog_post(db, post, update_data)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@authorize(required_role="admin")
def delete_blog_post_endpoint(
    post_id: UUID,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет BlogPost по UUID.

    Args:
        post_id (UUID): идентификатор поста
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        None

    Raises:
        HTTPException 404 - если пост не найден
        HTTPException 403 - если недостаточно прав для удаления
    """
    post = get_blogpost_or_404(post_id, db)
    delete_blog_post(db, post)
    return
