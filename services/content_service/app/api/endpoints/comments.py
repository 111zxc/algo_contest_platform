from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user, get_db
from app.schemas.comment import CommentCreate, CommentRead, CommentReadExtended
from app.services.comment import (
    create_comment,
    get_comment,
    list_comments_by_post,
    list_comments_by_user,
    list_enriched_comments_by_post,
    update_comment,
)
from app.services.user import get_user

router = APIRouter(prefix="/comments", tags=["comments"])


def get_comment_or_404(comment_id: str, db: Session = Depends(get_db)):
    comment = get_comment(db, comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Комментарий не найден"
        )
    return comment


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
@authorize(required_role="admin", owner_param="comment", owner_field="created_by")
def update_comment_endpoint(
    update_data: dict,
    comment: object = Depends(get_comment_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет заданные в body json поля комментария.
    Доступно для admin или автора комментария.
    """
    updated_comment = update_comment(db, comment, update_data)
    return updated_comment


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


@router.get("/post/enriched/{post_id}", response_model=list[CommentReadExtended])
def list_enriched_comments_by_post_endpoint(
    post_id: str,
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(
        10, ge=1, description="Максимальное число комментариев на страницу"
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает обогащённый список комментариев для поста с заданным post_id.

    Каждый комментарий содержит дополнительное поле author_display_name, полученное из таблицы пользователей.
    Пагинация реализована через параметры offset и limit.

    Args:
        post_id (str): Идентификатор поста.
        offset (int): Смещение для пагинации (по умолчанию 0).
        limit (int): Максимальное число возвращаемых записей (по умолчанию 10).
        db (Session): Сессия для работы с БД.

    Returns:
        List[CommentReadExtended]: Список обогащённых комментариев.
    """
    enriched_comments = list_enriched_comments_by_post(db, post_id, offset, limit)
    return enriched_comments
