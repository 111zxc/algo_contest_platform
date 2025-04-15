from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user
from app.api.endpoints.users import get_user_or_404
from app.core.database import get_db
from app.schemas.comment import CommentCreate, CommentRead, CommentReadWithReaction
from app.services.comment import (
    create_comment,
    get_comment,
    list_comments_by_post,
    list_comments_by_user,
    list_enriched_comments_by_post,
    update_comment,
)
from app.services.reaction import get_user_reaction

router = APIRouter(prefix="/comments", tags=["comments"])


def get_comment_or_404(comment_id: str, db: Session = Depends(get_db)):
    """
    Вспомогательная функция для @authorize, чтобы получать объект Comment через depends
    """
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
    Создает новый комментарий

    Args:
        comment_in (CommentCreate): данные для создания комментария
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        CommentRead - созданный комментарий
    """
    return create_comment(db, comment_in, user_id=user_claims.get("sub"))


@router.get("/{comment_id}", response_model=CommentRead)
def read_comment_endpoint(comment_id: str, db: Session = Depends(get_db)):
    """
    Возвращает комментарий по его идентификатору

    Args:
        comment_id (str): идентификатор комментария
        db (Session): объект сессии БД

    Returns:
        CommentRead - найденный комментарий

    Raises:
        HTTPException 404 - если комментарий не найден
    """
    return get_comment_or_404(db, comment_id)


@router.put("/{comment_id}", response_model=CommentRead)
@authorize(required_role="admin", owner_param="comment", owner_field="created_by")
def update_comment_endpoint(
    update_data: dict,
    comment: object = Depends(get_comment_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет данные комментария

    Args:
        update_data (dict): данные для обновления комментария
        comment (Comment): объект комментария, который требуется обновить
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        CommentRead - обновленный комментарий

    Raises:
        HTTPException 404 - если комментарий не найден
        HTTPException 403 - если недостаточно прав для обновления
    """
    return update_comment(db, comment, update_data)


@router.get("/post/{post_id}", response_model=list[CommentRead])
def list_comments_by_post_endpoint(post_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список комментариев для указанного поста

    Args:
        post_id (str): идентификатор поста
        db (Session): объект сессии БД

    Returns:
        list[CommentRead] - список комментариев для поста
    """
    return list_comments_by_post(db, post_id)


@router.get("/user/{user_id}", response_model=list[CommentRead])
def list_comments_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список комментариев, оставленных указанным пользователем

    Args:
        user_id (str): идентификатор пользователя
        db (Session): объект сессии БД

    Returns:
        list[CommentRead] - список комментариев, оставленных пользователем

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    local_user = get_user_or_404(user_id, db)
    return list_comments_by_user(db, local_user.keycloak_id)


@router.get("/post/enriched/{post_id}", response_model=list[CommentReadWithReaction])
def list_enriched_comments_by_post_endpoint(
    post_id: str,
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(
        10, ge=1, description="Максимальное число комментариев на страницу"
    ),
    current_user_id: str | None = Query(
        None,
        description="Опциональный Keycloak ID пользователя для поиска его реакции на комментарии",
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает список комментариев (CommentReadExtended) для указанного поста
    Пагинация реализована через параметры offset и limit

    Args:
        post_id (str): идентификатор поста
        offset (int): смещение для выборки (по умолчанию 0)
        limit (int): максимальное число задач на страницу (по умолчанию 10)
        current_user_id (optional, str): идентификатор пользователя
        db (Session): сессия для работы с базой данных

    Returns:
        List[ProblemReadExtended]: список задач.
    """
    enriched_comments = list_enriched_comments_by_post(db, post_id, offset, limit)

    if current_user_id:
        for comment in enriched_comments:
            reaction = get_user_reaction(
                db, str(comment.id), "comment", current_user_id
            )
            if reaction:
                setattr(comment, "user_reaction", reaction.reaction_type)
            else:
                setattr(comment, "user_reaction", None)

    return [CommentReadWithReaction.from_orm(comment) for comment in enriched_comments]
