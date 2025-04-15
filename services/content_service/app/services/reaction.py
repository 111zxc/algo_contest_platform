from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.reaction import Reaction
from app.schemas.reaction import ReactionCreate, ReactionType, TargetType


def create_reaction(db: Session, reaction_in: ReactionCreate) -> Reaction:
    """
    Создает и возвращает объект реакции, используя переданные данные

    Args:
        db (Session): объект сессии БД
        reaction_in (ReactionCreate): объект с данными для создания реакции

    Returns:
        Reaction - созданная реакция
    """
    reaction = Reaction(
        created_by=reaction_in.user_id,
        target_id=reaction_in.target_id,
        target_type=reaction_in.target_type,
        reaction_type=reaction_in.reaction_type,
    )
    try:
        db.add(reaction)
        db.commit()
        db.refresh(reaction)
    except Exception as e:
        logger.error(
            f"Couldn't create reaction for {reaction.target_type} with id: {reaction.target_id} by {reaction.created_by}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Successfully created reaction for {reaction.target_type} with id: {reaction.target_id} by {reaction.created_by}"
        )
    return reaction


def get_reaction(db: Session, reaction_id: str) -> Reaction | None:
    """
    Возвращает объект реакции по идентификатору или None, если реакция не найдена

    Args:
        db (Session): объект сессии БД
        reaction_id (str): идентификатор реакции

    Returns:
        Reaction | None - найденная реакция или None, если реакции не существует
    """
    try:
        result = db.query(Reaction).filter(Reaction.id == reaction_id).first()
    except Exception as e:
        logger.error(f"Error getting reaction with id {reaction_id}: {str(e)}")
        raise
    else:
        if result is None:
            logger.warning(f"Couldn't get reaction with id {reaction_id}")
        else:
            logger.info(f"Successfully got reaction with id {reaction_id}")
        return result


def delete_reaction(db: Session, reaction: Reaction) -> None:
    """
    Удаляет запись реакции

    Args:
        db (Session): объект сессии БД
        reaction (Reaction): объект реакции для удаления

    Returns:
        None
    """
    try:
        db.delete(reaction)
        db.commit()
    except Exception as e:
        logger.error(f"Couldn't delete reaction with id: {reaction.id}: {str(e)}")
        raise
    else:
        logger.info(f"Successfully deleted reaction with id: {reaction.id}")


def set_reaction(
    db: Session,
    target_id: str,
    target_type: TargetType,
    reaction_type: ReactionType,
    user_id: str,
) -> Reaction | None:
    """
    Устанавливает реакцию пользователя на целевой объект
    Если пользователь повторно ставит ту же реакцию, то реакция удаляется и функция возвращает None
    Если реакция противоположная, старая удаляется, и создается новая реакция

    Args:
        db (Session): объект сессии БД
        target_id (str): идентификатор целевого объекта
        target_type (TargetType): тип целевого объекта ("post", "comment", "problem")
        reaction_type (ReactionType): тип реакции ("plus" или "minus")
        user_id (str): User.Keycloak_id

    Returns:
        Reaction | None - объект реакции, если создана новая реакция, или None, если реакция удалена
    """
    try:
        existing_reaction = (
            db.query(Reaction)
            .filter(
                Reaction.target_id == target_id,
                Reaction.target_type == target_type,
                Reaction.created_by == user_id,
            )
            .first()
        )
    except Exception as e:
        logger.error(
            f"Error fetching existing reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
        )
        raise

    # Если реакция существует
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            try:
                db.delete(existing_reaction)
                db.commit()
            except Exception as e:
                logger.error(
                    f"Couldn't remove existing reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
                )
                raise
            return None

        elif existing_reaction.reaction_type != reaction_type:
            try:
                db.delete(existing_reaction)
                db.commit()
            except Exception as e:
                logger.error(
                    f"Couldn't update reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
                )
                raise
            try:
                new_reaction = Reaction(
                    created_by=user_id,
                    target_id=target_id,
                    target_type=target_type,
                    reaction_type=reaction_type,
                )
                db.add(new_reaction)
                db.commit()
                db.refresh(new_reaction)
            except Exception as e:
                logger.error(
                    f"Couldn't create new reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
                )
                raise
            return new_reaction

    # Если реакции нет, создаем новую
    try:
        new_reaction = Reaction(
            created_by=user_id,
            target_id=target_id,
            target_type=target_type,
            reaction_type=reaction_type,
        )
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
    except Exception as e:
        logger.error(
            f"Couldn't set new reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Successfully set new reaction for {target_type} with id: {target_id} by {user_id}"
        )
    return new_reaction


def list_reactions_for_target(
    db: Session, target_id: str, target_type: str
) -> list[Reaction]:
    """
    Возвращает список всех реакций для объекта с заданными target_id и target_type

    Args:
        db (Session): объект сессии БД
        target_id (str): идентификатор целевого объекта
        target_type (str): тип целевого объекта ("post", "comment", "problem")

    Returns:
        list[Reaction] - список реакций для данного объекта
    """
    try:
        reactions = (
            db.query(Reaction)
            .filter(
                Reaction.target_id == target_id, Reaction.target_type == target_type
            )
            .all()
        )
    except Exception as e:
        logger.error(
            f"Couldn't get reactions for {target_type} with id: {target_id}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Successfully got all {len(reactions)} reactions for {target_type} with id: {target_id}"
        )
    return reactions


def compute_reaction_balance(db: Session, target_id: str, target_type: str) -> int:
    """
    Вычисляет и возвращает баланс реакций для объекта с заданными target_id и target_type

    Args:
        db (Session): объект сессии БД
        target_id (str): идентификатор объекта (задачи, поста или комментария)
        target_type (str): тип объекта ("post", "comment" или "problem")

    Returns:
        int - баланс реакций (сумма +1 за plus, -1 за minus)
    """
    try:
        reactions = (
            db.query(Reaction)
            .filter(
                Reaction.target_id == target_id, Reaction.target_type == target_type
            )
            .all()
        )
    except Exception as e:
        logger.error(
            f"Couldn't compute reaction balance for {target_type} with id: {target_id}: {str(e)}"
        )
        raise
    balance = 0
    for r in reactions:
        if r.reaction_type == ReactionType.plus:
            balance += 1
        elif r.reaction_type == ReactionType.minus:
            balance -= 1
    logger.info(
        f"Successfully computed reaction balance ({balance}) for {target_type} {target_id}"
    )
    return balance


def get_user_reaction(
    db: Session, target_id: str, target_type: str, user_id: str
) -> Reaction | None:
    """
    Возвращает реакцию пользователя по target_id и target_type, если она существует

    Args:
        db (Session): объект сессии БД
        target_id (str): идентификатор целевого объекта
        target_type (str): тип целевого объекта ("problem", "post", "comment")
        user_id (str): User.keycloak_id пользователя

    Returns:
        Reaction | None - объект реакции или None, если реакции нет
    """
    try:
        reaction = (
            db.query(Reaction)
            .filter(
                Reaction.target_id == target_id,
                Reaction.target_type == target_type,
                Reaction.created_by == user_id,
            )
            .first()
        )
    except Exception as e:
        logger.error(
            f"Couldn't get user reaction for {target_type} with id: {target_id} by user {user_id}: {str(e)}"
        )
        raise
    else:
        logger.info(
            f"Succesfully got user {user_id}'s reaction to {target_type} {target_id}"
        )
    return reaction
