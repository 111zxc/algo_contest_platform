from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user, get_db
from app.schemas.post import PostCreate, PostRead, PostReadExtended
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
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_or_404(post_id: str, db: Session = Depends(get_db)):
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост не найден"
        )
    return post


@router.post("/", response_model=PostRead)
def create_post_endpoint(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Для создания постов к задачам
    """
    user_id = user_claims.get("sub")
    post = create_post(db, post_in, user_id)
    return post


@router.get("/{post_id}", response_model=PostRead)
def read_post_endpoint(post_id: str, db: Session = Depends(get_db)):
    """
    без авторизации ворзвращает app.schemas.post.PostRead
    или 404, если пост по id не найден
    """
    return get_post_or_404(post_id, db)


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
    Доступ разрешён, если пользователь обладает ролью admin или является автором поста (post.user_id).
    Возвращает обновлённые данные (PostRead) или ошибку:
      - 404, если пост не найден;
      - 403, если недостаточно прав.
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
    Возвращает list[PostRead] всех постов, 200
    """
    posts = list_posts(db)
    return posts


@router.get("/by-user/{user_id}", response_model=list[PostRead])
def list_posts_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    user_id — локальный идентификатор пользователя.
    Для фильтрации постов используется keycloak_id, поэтому сначала получаем локального пользователя.
    """
    local_user = get_user(db, user_id)
    if not local_user:
        raise HTTPException(status_code=404, detail="User not found")
    posts = list_posts_by_user(db, local_user.keycloak_id)
    return posts


@router.get("/by-problem/{problem_id}", response_model=list[PostRead])
def list_posts_by_problem_endpoint(problem_id: str, db: Session = Depends(get_db)):
    """
    Возвращает все посты, созданные от задачи problem_id
    list[PostRead], 200
    """
    posts = list_posts_by_problem(db, problem_id)
    return posts


@router.get("/by-tag/{tag_id}", response_model=list[PostRead])
def list_posts_by_tag_endpoint(tag_id: str, db: Session = Depends(get_db)):
    """
    Возвращает все пост по тегу tag_id
    list[PostRead],  200
    """
    posts = list_posts_by_tag(db, tag_id)
    return posts

@router.get("/by-problem/enriched/{problem_id}", response_model=list[PostReadExtended])
def list_enriched_posts_by_problem_endpoint(
    problem_id: str,
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, description="Максимальное число постов на страницу"),
    db: Session = Depends(get_db)
):
    """
    Возвращает список постов для задачи problem_id с добавленным полем author_display_name.
    Реализована пагинация через параметры offset и limit.

    Args:
        problem_id (str): Идентификатор задачи.
        offset (int): Смещение для выборки (по умолчанию 0).
        limit (int): Максимальное количество возвращаемых записей (по умолчанию 10).
        db (Session): Сессия для работы с БД.

    Returns:
        List[PostReadExtended]: Обогащенный список постов.
    """
    enriched_posts = list_enriched_posts_by_problem(db, problem_id, offset, limit)
    return enriched_posts