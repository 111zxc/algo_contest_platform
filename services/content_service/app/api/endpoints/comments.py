from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.comment import CommentCreate, CommentRead
from app.services.comment import (
    create_comment,
    get_comment,
    list_comments_by_post,
    list_comments_by_user,
    update_comment,
)
from app.services.user import get_user

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentRead)
def create_comment_endpoint(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Для создания комментария
    """
    comment = create_comment(db, comment_in, user_id=user_claims.get("sub"))
    return comment


@router.get("/{comment_id}", response_model=CommentRead)
def read_comment_endpoint(comment_id: str, db: Session = Depends(get_db)):
    """
    Возвращает app.schemas.comments.CommentRead, 200
    или 404, если коммент по id не найден
    """
    comment = get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )
    return comment


@router.put("/{comment_id}", response_model=CommentRead)
def update_comment_endpoint(
    comment_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет заданные в body json поля коммента
    admin/author комментария
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    comment = get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if comment.user_id != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this comment",
        )
    comment = update_comment(db, comment, update_data)
    return comment


@router.get("/post/{post_id}", response_model=list[CommentRead])
def list_comments_by_post_endpoint(post_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список комментариев к посту post_id
    list[CommentRead],  200
    """
    comments = list_comments_by_post(db, post_id)
    return comments


@router.get("/user/{user_id}", response_model=list[CommentRead])
def list_comments_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список комментариев, оставленных пользователем user_id
    list[CommentRead], 200
    404, если пользователь по user_id не найден.
    """
    local_user = get_user(db, user_id)
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    comments = list_comments_by_user(db, local_user.keycloak_id)
    return comments
