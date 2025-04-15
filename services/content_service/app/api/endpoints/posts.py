from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user
from app.api.endpoints.users import get_user_or_404
from app.core.database import get_db
from app.models.post import Post
from app.schemas.post import (
    PostCreate,
    PostRead,
    PostReadExtended,
    PostReadWithReaction,
)
from app.services.post import (
    create_post,
    delete_post,
    get_post,
    list_enriched_posts_by_problem,
    list_posts,
    list_posts_by_problem,
    list_posts_by_tag,
    list_posts_by_user,
    update_post,
)
from app.services.reaction import compute_reaction_balance, get_user_reaction
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_or_404(post_id: str, db: Session = Depends(get_db)) -> Post:
    """
    Вспомогательная функция для @authorize, чтобы получать объект Post через depends
    """
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post can't be found"
        )
    return post


@router.post("/", response_model=PostRead)
def create_post_endpoint(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Создает новый пост для задачи

    Args:
        post_in (PostCreate): данные для создания поста
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        PostRead - созданный пост
    """
    user_id = user_claims.get("sub")
    post = create_post(db, post_in, user_id)
    return post


@router.get("/{post_id}", response_model=PostReadWithReaction)
def read_post_endpoint(
    post_id: str,
    db: Session = Depends(get_db),
    current_user_id: str | None = Query(
        None,
        description="Опционально, ID пользователя для получения его реакции на пост",
    ),
):
    """
    Возвращает пост по его id в виде схемы PostReadWithReaction

    Returns:
      PostReadWithReaction - если пост найден, фетч поста для фронта

    Args:
        post_id (str): идентификатор поста
        db (Session): сессия для работы с базой данных
        current_user_id (str, optional): User.keycloak_id пользователя для поиска его реакции

    Raises:
        HTTPException: 404, если пост не найден
    """
    post = get_post_or_404(post_id, db)

    user_obj = get_user(db, post.created_by)
    author_display_name = user_obj.display_name if user_obj else None

    reaction_balance = compute_reaction_balance(db, str(post.id), "post")

    user_reaction = None
    if current_user_id:
        reaction = get_user_reaction(db, str(post.id), "post", current_user_id)
        if reaction:
            user_reaction = reaction.reaction_type

    response = PostReadWithReaction.from_orm(post)
    response.author_display_name = author_display_name
    response.reaction_balance = reaction_balance
    response.user_reaction = user_reaction

    return response


@router.put("/{post_id}", response_model=PostRead)
@authorize(required_role="admin", owner_param="post", owner_field="created_by")
def update_post_endpoint(
    update_data: dict,
    post: object = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет данные поста.
    Доступ разрешён, если пользователь имеет роль admin или является автором поста

    Args:
        update_data (dict): словарь с данными для обновления поста
        post (Post): объект поста для обновления
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        PostRead - обновлённый пост

    Raises:
        HTTPException 404 - если пост не найден
        HTTPException 403 - если недостаточно прав
    """
    updated_post = update_post(db, post, update_data)
    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="post", owner_field="created_by")
def delete_post_endpoint(
    post: object = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет запись поста

    Args:
        post (Post): объект поста для удаления
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        None

    Raises:
        HTTPException 404 - если пост не найден
    """
    delete_post(db, post)
    return


@router.post("/{post_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="post", owner_field="created_by")
def attach_tag_to_post(
    tag_id: UUID,
    post: object = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Прикрепляет тег к посту

    Args:
        tag_id (UUID): идентификатор тега для прикрепления
        post (Post): объект поста для обновления
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        None

    Raises:
        HTTPException 404 - если тег не найден
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    post.tags.append(tag)
    db.commit()
    return None


@router.delete("/{post_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="post", owner_field="created_by")
def detach_tag_from_post(
    tag_id: UUID,
    post: object = Depends(get_post_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Открепляет тег от поста

    Args:
        tag_id (UUID): идентификатор тега для отсоединения
        post (Post): объект поста для обновления
        db (Session): объект сессии БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        None

    Raises:
        HTTPException 404 - если тег не найден
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    post.tags.remove(tag)
    db.commit()
    return None


@router.get("/", response_model=list[PostRead])
def list_all_posts(db: Session = Depends(get_db)):
    """
    Возвращает список всех постов

    Args:
        db (Session): объект сессии БД

    Returns:
        list[PostRead] - список постов
    """
    posts = list_posts(db)
    return posts


@router.get("/by-user/{user_id}", response_model=list[PostRead])
def list_posts_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список постов, созданных указанным пользователем

    Args:
        user_id (str): локальный идентификатор пользователя (Keycloak ID)
        db (Session): объект сессии БД

    Returns:
        list[PostRead] - список постов, созданных пользователем

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    local_user = get_user_or_404(user_id, db)
    posts = list_posts_by_user(db, local_user.keycloak_id)
    return posts


@router.get("/by-problem/{problem_id}", response_model=list[PostRead])
def list_posts_by_problem_endpoint(problem_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список постов, связанных с указанной задачей

    Args:
        problem_id (str): идентификатор задачи
        db (Session): объект сессии БД

    Returns:
        list[PostRead] - список постов для задачи
    """
    posts = list_posts_by_problem(db, problem_id)
    return posts


@router.get("/by-tag/{tag_id}", response_model=list[PostRead])
def list_posts_by_tag_endpoint(tag_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список постов по указанному тегу.

    Args:
        tag_id (str): идентификатор тега
        db (Session): объект сессии БД

    Returns:
        list[PostRead] - список постов с заданным тегом
    """
    posts = list_posts_by_tag(db, tag_id)
    return posts


@router.get("/by-problem/enriched/{problem_id}", response_model=list[PostReadExtended])
def list_enriched_posts_by_problem_endpoint(
    problem_id: str,
    offset: int = Query(0, ge=0, description="Смещение для выборки"),
    limit: int = Query(10, ge=1, description="Максимальное число постов на страницу"),
    tag_id: str | None = Query(None, description="Фильтр по идентификатору тега"),
    sort_by_rating: bool = Query(False, description="Сортировать по рейтингу"),
    sort_order: str = Query(
        "desc", description="Направление сортировки: 'asc' или 'desc'"
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает список задач (PostReadExtended) для указанной задачи
    Пагинация реализована через параметры offset и limit
    Дополнительно можно фильтровать посты по тегу, сортировать по рейтингу

    Args:
        problem_id (str): идентификатор задачи
        offset (int): смещение для выборки (по умолчанию 0)
        limit (int): максимальное число задач на страницу (по умолчанию 10)
        tag_id (optional, str): фильтр по идентификатору тега
        sort_by_rating (bool): если True, сортирует задачи по рейтингу (reaction_balance)
        sort_order (str): направление сортировки ("asc", "desc")
        db (Session): сессия для работы с базой данных

    Returns:
        List[ProblemReadExtended]: список задач.
    """
    enriched_posts = list_enriched_posts_by_problem(
        db, problem_id, offset, limit, tag_id, sort_by_rating, sort_order
    )
    return enriched_posts
