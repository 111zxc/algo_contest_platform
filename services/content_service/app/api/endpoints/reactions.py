from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.reaction import (
    ReactionCreate,
    ReactionListResponse,
    ReactionRead,
    TargetType,
)
from app.services.reaction import (
    compute_reaction_balance,
    get_reaction,
    list_reactions_for_target,
    set_reaction,
)

router = APIRouter(prefix="/reactions", tags=["reactions"])


@router.get("/by-target", response_model=ReactionListResponse)
def list_reactions_for_target_endpoint(
    target_id: str = Query(
        ..., description="Идентификатор целевого объекта (поста или комментария)"
    ),
    target_type: TargetType = Query(
        ..., description="Тип целевого объекта ('post', 'comment')"
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает список реакций для указанного target и суммарный баланс.
    Баланс рассчитывается как: +1 за 'plus' и -1 за 'minus'.

    Args:
        target_id (str): идентификатор целевого объекта
        target_type (TargetType): тип целевого объекта ('post', 'comment')
        db (Session): объект сессии БД

    Returns:
        ReactionListResponse - объект, содержащий суммарный баланс реакций и список реакций
    """
    reactions = list_reactions_for_target(db, target_id, target_type)
    balance = compute_reaction_balance(db, target_id, target_type)
    return {"balance": balance, "reactions": reactions}


@router.post("/", response_model=ReactionRead)
def set_reaction_endpoint(
    reaction_in: ReactionCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
    response: Response = None,
):
    """
    Ставит реакцию на указанный таргет

    Args:
        reaction_in (ReactionCreate): объект с данными для создания реакции
        db (Session): объект сессии БД
        user_claims (dict): данные авторизации пользователя, извлеченные из токена

    Returns:
        ReactionRead - созданная или измененная реакция,
        либо HTTP 204 No Content, если реакция удалена
    """
    user_id = user_claims.get("sub")
    result = set_reaction(
        db,
        reaction_in.target_id,
        reaction_in.target_type,
        reaction_in.reaction_type,
        user_id,
    )
    if result is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return result


@router.get("/{reaction_id}", response_model=ReactionRead)
def read_reaction_endpoint(reaction_id: str, db: Session = Depends(get_db)):
    """
    Возвращает реакцию по её идентификатору

    Args:
        reaction_id (str): идентификатор реакции
        db (Session): объект сессии БД

    Returns:
        ReactionRead - найденная реакция

    Raises:
        HTTPException 404 - если реакция не найдена
    """
    reaction = get_reaction(db, reaction_id)
    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found"
        )
    return reaction
