from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.reaction import Reaction
from app.schemas.reaction import ReactionCreate, ReactionType, TargetType


def create_reaction(db: Session, reaction_in: ReactionCreate) -> Reaction:
    reaction = Reaction(
        created_by=reaction_in.user_id,
        target_id=reaction_in.target_id,
        target_type=reaction_in.target_type,
        reaction_type=reaction_in.reaction_type,
    )
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    logger.info(
        f"Succesfully created reaction for {reaction.target_type} with id: {reaction.target_id} by {reaction.created_by}"
    )
    return reaction


def get_reaction(db: Session, reaction_id: str) -> Reaction | None:
    result = db.query(Reaction).filter(Reaction.id == reaction_id).first()
    if result is None:
        logger.info(f"Couldn't get reaction with id {reaction_id}")
    else:
        logger.info(f"Succesfully got reaction with id {reaction_id}")
    return result


def delete_reaction(db: Session, reaction: Reaction) -> None:
    db.delete(reaction)
    db.commit()
    logger.info(f"Succesfully deleted reaction with id:{reaction.id}")


def set_reaction(
    db: Session,
    target_id: str,
    target_type: TargetType,
    reaction_type: ReactionType,
    user_id: str,
) -> Reaction:
    # Проверяем, существует ли уже реакция пользователя для этого объекта (поста или комментария)
    existing_reaction = (
        db.query(Reaction)
        .filter(
            Reaction.target_id == target_id,
            Reaction.target_type == target_type,
            Reaction.created_by == user_id,
        )
        .first()
    )

    if existing_reaction:
        # Если реакция существует и такая же, удаляем её
        if existing_reaction.reaction_type == reaction_type:
            db.delete(existing_reaction)
            db.commit()
            return {"detail": "Reaction was deleted succesfully"}

        # Если реакция противоположная, удаляем старую и создаем новую
        if existing_reaction.reaction_type != reaction_type:
            db.delete(existing_reaction)
            db.commit()
            # Создаем новую реакцию
            new_reaction = Reaction(
                created_by=user_id,
                target_id=target_id,
                target_type=target_type,
                reaction_type=reaction_type,
            )
            db.add(new_reaction)
            db.commit()
            db.refresh(new_reaction)
            return new_reaction

    # Если реакции нет, создаем новую
    new_reaction = Reaction(
        created_by=user_id,
        target_id=target_id,
        target_type=target_type,
        reaction_type=reaction_type,
    )
    db.add(new_reaction)
    db.commit()
    db.refresh(new_reaction)
    logger.info(
        f"Succesfully set new reaction for {target_type} with id: {target_id} by {user_id}"
    )
    return new_reaction


def list_reactions_for_target(
    db: Session, target_id: str, target_type: str
) -> list[Reaction]:
    logger.info(f"Succesfully got all reactions for {target_type} with id: {target_id}")
    return (
        db.query(Reaction)
        .filter(Reaction.target_id == target_id, Reaction.target_type == target_type)
        .all()
    )


def compute_reaction_balance(reactions: list[Reaction]) -> int:
    balance = 0
    for reaction in reactions:
        if reaction.reaction_type == ReactionType.plus:
            balance += 1
        elif reaction.reaction_type == ReactionType.minus:
            balance -= 1
    return balance
