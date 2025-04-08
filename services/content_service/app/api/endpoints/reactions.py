from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
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
        ..., description="Тип целевого объекта ('post' или 'comment')"
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает список реакций для указанного target и суммарный баланс.
    Баланс рассчитывается как: +1 за 'plus' и -1 за 'minus'.
    """
    reactions = list_reactions_for_target(db, target_id, target_type)
    balance = compute_reaction_balance(reactions)
    return {"balance": balance, "reactions": reactions}


@router.post("/", response_model=ReactionRead)
def set_reaction_endpoint(
    reaction_in: ReactionCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Ставит реакцию на указанный пост/комментарий.
    Учитывает, если реакция уже поставлена
    """
    user_id = user_claims.get("sub")
    reaction = set_reaction(
        db,
        reaction_in.target_id,
        reaction_in.target_type,
        reaction_in.reaction_type,
        user_id,
    )
    return reaction


@router.get("/{reaction_id}", response_model=ReactionRead)
def read_reaction_endpoint(reaction_id: str, db: Session = Depends(get_db)):
    reaction = get_reaction(db, reaction_id)
    if not reaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found"
        )
    return reaction
