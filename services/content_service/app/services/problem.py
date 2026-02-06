from sqlalchemy import case, func
from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
from app.models.problem import Problem
from app.models.reaction import Reaction, ReactionType
from app.models.user import User
from app.schemas.problem import ProblemCreate


def create_problem(db: Session, problem_in: ProblemCreate, creator_id: str) -> Problem:
    """
    Создает и возвращает объект задачи, используя переданные данные

    Args:
        db (Session): объект сессии БД
        problem_in (ProblemCreate): объект с данными для создания задачи
        creator_id (str): ID пользователя, создавшего задачу

    Returns:
        Problem - созданная задача
    """
    test_cases_dict = (
        [test_case.to_dict() for test_case in problem_in.test_cases]
        if problem_in.test_cases
        else []
    )

    problem = Problem(
        title=problem_in.title,
        description=problem_in.description,
        difficulty=problem_in.difficulty,
        created_by=creator_id,
        test_cases=test_cases_dict,
        time_limit=problem_in.time_limit,
        memory_limit=problem_in.memory_limit,
        contest_id=problem_in.contest_id
    )
    try:
        db.add(problem)
        db.commit()
        db.refresh(problem)
    except Exception:
        logger.exception("problem_create_failed",
                         extra={'owner_id': creator_id})
        db.rollback()
        raise
    else:
        logger.debug("problem_create",
                     extra={'problem_id': str(problem.id)})
    return problem


def get_problem(db: Session, problem_id: str) -> Problem | None:
    """
    Возвращает объект задачи по идентификатору или None, если задача не найдена

    Args:
        db (Session): объект сессии БД
        problem_id (str): идентификатор задачи

    Returns:
        Problem | None - найденная задача или None, если задача не существует
    """
    try:
        result = (
            db.query(Problem)
            .filter(Problem.id == problem_id)
            .options(joinedload(Problem.tags))
            .first()
        )
    except Exception:
        logger.exception("problem_get_failed",
                         extra={'problem_id': problem_id})
        raise
    else:
        if result is None:
            logger.warning("problem_get_notfound",
                           extra={'problem_id': problem_id})
        else:
            logger.debug("problem_get",
                         extra={'problem_id': problem_id})
    return result


def update_problem(db: Session, problem: Problem, update_data: dict) -> Problem:
    """
    Обновляет данные задачи и возвращает обновленный объект задачи.

    Args:
        db (Session): объект сессии БД
        problem (Problem): объект задачи для обновления
        update_data (dict): словарь с данными для обновления

    Returns:
        Problem - обновленная задача
    """
    for key, value in update_data.items():
        if key != 'tags':
            setattr(problem, key, value)
    try:
        db.commit()
        db.refresh(problem)
    except Exception:
        logger.exception("problem_update_failed",
                         extra={'problem_id': str(problem.id), 'created_by': str(problem.created_by)})
        db.rollback()
        raise
    else:
        logger.debug("problem_update",
                     extra={'problem_id': str(problem.id)})
    return problem


def delete_problem(db: Session, problem: Problem) -> None:
    """
    Удаляет запись задачи

    Args:
        db (Session): объект сессии БД
        problem (Problem): объект задачи для удаления

    Returns:
        None - функция ничего не возвращает
    """
    try:
        db.delete(problem)
        db.commit()
    except Exception:
        logger.exception("problem_delete_failed",
                         extra={'problem_id': str(problem.id), 'created_by': str(problem.created_by)})
        db.rollback()
        raise
    else:
        logger.debug("problem_delete",
                     extra={'problem_id': str(problem.id)})


def list_problems(db: Session) -> list[Problem]:
    """
    Возвращает список всех задач

    Args:
        db (Session): объект сессии БД

    Returns:
        list[Problem] - список задач
    """
    try:
        problems = db.query(Problem).options(joinedload(Problem.tags)).all()
    except Exception:
        logger.exception("problem_list_failed")
        raise
    else:
        logger.debug("problem_list",
                     extra={'length': len(problems)})
    return problems


def list_problems_by_tag(db: Session, tag_id: str) -> list[Problem]:
    """
    Возвращает список задач, имеющих тег с заданным идентификатором

    Args:
        db (Session): объект сессии БД
        tag_id (str): идентификатор тега

    Returns:
        list[Problem] - список задач с данным тегом
    """
    try:
        problems = (
            db.query(Problem)
            .options(joinedload(Problem.tags))
            .filter(Problem.tags.any(id=tag_id))
            .all()
        )
    except Exception:
        logger.exception("problem_listtag_failed",
                         extra={'tag_id': tag_id})
        raise
    else:
        logger.debug("problem_listtag",
                     extra={'tag_id': tag_id, 'length': len(problems)})
    return problems


def list_problems_by_user(db: Session, user_id: str) -> list[Problem]:
    """
    Возвращает список задач, созданных указанным пользователем

    Args:
        db (Session): объект сессии БД
        user_id (str): идентификатор пользователя

    Returns:
        list[Problem] - список задач, созданных пользователем
    """
    try:
        problems = (
            db.query(Problem)
            .options(joinedload(Problem.tags))
            .filter(Problem.created_by == user_id)
            .all()
        )
    except Exception:
        logger.exception("problem_listuser_failed",
                         extra={'user_id': user_id, 'length': len(problems)})
        raise
    else:
        logger.debug("problem_listuser",
                     extra={'user_id': user_id, 'length': len(problems)})
    return problems


def list_problems_by_difficulty(db: Session, difficulty: str) -> list[Problem]:
    """
    Возвращает список задач с заданной сложностью

    Args:
        db (Session): объект сессии БД
        difficulty (str): уровень сложности задачи

    Returns:
        list[Problem] - список задач с указанной сложностью
    """
    try:
        problems = (
            db.query(Problem)
            .options(joinedload(Problem.tags))
            .filter(Problem.difficulty == difficulty)
            .all()
        )
    except Exception:
        logger.exception("problems_listdifficulty_failed",
                         extra={'difficulty': difficulty})
        raise
    else:
        logger.debug('problems_listdifficulty',
                     extra={'difficulty': difficulty, 'length': len(problems)})
    return problems


def list_enriched_problems_filtered(
    db: Session,
    offset: int = 0,
    limit: int = 10,
    difficulty: str | None = None,
    tag_id: str | None = None,
    sort_by_rating: bool = False,
    sort_order: str = "desc",  # "asc", "desc"
) -> list[Problem]:
    """
    Возвращает список задач с дополнительными полями author_display_name, reaction_balance; ..
    .. с использованием пагинации, фильтрацией по сложности и тегу; сортировкой по рейтингу

    Args:
        db (Session): сессия базы данных
        offset (int): смещение для пагинации
        limit (int): количество задач на страницу
        difficulty (Optional[str]): опционально, фильтрует задачи по сложности ("EASY", "MEDIUM", "HARD")
        tag_id (Optional[str]): опционально, фильтрует задачи, имеющие тег с данным Tag.id
        sort_by_rating (bool): если True, сортирует результаты по рейтингу
        sort_order (str): направление сортировки ("asc", "desc"), по умолчанию "desc".

    Returns:
        List[Problem] - список задач с указанными параметрами
    """
    try:
        reaction_subq = (
            db.query(
                Reaction.target_id.label("problem_id"),
                func.sum(
                    case(
                        (Reaction.reaction_type == ReactionType.plus, 1),
                        (Reaction.reaction_type == ReactionType.minus, -1),
                        else_=0,
                    )
                ).label("balance"),
            )
            .filter(Reaction.target_type == "problem")
            .group_by(Reaction.target_id)
            .subquery()
        )
    except Exception:
        logger.exception("problem_listenriched_failed",
                     extra={'detail': 'could not compute reaction subquery'})
        raise

    try:
        query = (
            db.query(Problem, User.display_name, reaction_subq.c.balance)
            .join(User, Problem.created_by == User.keycloak_id)
            .outerjoin(reaction_subq, Problem.id == reaction_subq.c.problem_id)
        )

        if difficulty:
            query = query.filter(Problem.difficulty == difficulty)
        if tag_id:
            query = query.filter(Problem.tags.any(id=tag_id))
        query = query.filter(Problem.contest_id.is_(None))

        if sort_by_rating:
            if sort_order == "asc":
                query = query.order_by(func.coalesce(reaction_subq.c.balance, 0).asc())
            else:
                query = query.order_by(func.coalesce(reaction_subq.c.balance, 0).desc())

        query = query.offset(offset).limit(limit)
        results = query.all()
    except Exception:
        logger.exception("problem_listenriched_failed")
        raise

    enriched = []
    for problem, display_name, balance in results:
        setattr(problem, "author_display_name", display_name)
        setattr(problem, "reaction_balance", balance if balance is not None else 0)
        enriched.append(problem)
    logger.debug("problem_listenriched",
                 extra={'length': len(enriched)})
    return enriched
