from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.post import PostCreate, PostRead
from app.services.post import (
    create_post,
    delete_post,
    get_post,
    list_posts,
    list_posts_by_problem,
    list_posts_by_tag,
    list_posts_by_user,
    update_post,
)
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/posts", tags=["posts"])


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
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post


@router.put("/{post_id}", response_model=PostRead)
def update_post_endpoint(
    post_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет данные в body json поля задачи, возвращает обновленные данные ..
    .. в app.schemas.post.PostRead
    или 404, если не найден
    или 403, если не admin/author
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.user_id != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this post",
        )

    post = update_post(db, post, update_data)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post_endpoint(
    post_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет задачу, отдает 204
    404, когда пост по id не найден
    403, если не admin/author
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if post.user_id != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this post",
        )

    delete_post(db, post)
    return


@router.post("/{post_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def attach_tag_to_post(
    post_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Прикрепляет тег к посту, 204
    404, если тег или пост не найден
    403, если не admin/author поста
    """
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    current_keycloak_id = user_claims.get("sub")
    if post.user_id != current_keycloak_id and "admin" not in user_claims.get(
        "realm_access", {}
    ).get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this post",
        )

    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    post.tags.append(tag)
    db.commit()
    return None


@router.delete("/{post_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag_from_post(
    post_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Открепляет тег от поста, 204
    404, если пост или тег не найден
    403, если не admin/author поста
    """
    post = get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    current_keycloak_id = user_claims.get("sub")
    if post.user_id != current_keycloak_id and "admin" not in user_claims.get(
        "realm_access", {}
    ).get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this post",
        )

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
