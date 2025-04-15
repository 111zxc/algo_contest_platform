from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user
from app.api.endpoints.users import get_user_or_404
from app.core.database import get_db
from app.models.problem import Problem
from app.schemas.problem import (
    ProblemCreate,
    ProblemRead,
    ProblemReadExtended,
    ProblemReadWithReaction,
)
from app.services.problem import (
    create_problem,
    delete_problem,
    get_problem,
    list_enriched_problems_filtered,
    list_problems,
    list_problems_by_difficulty,
    list_problems_by_tag,
    list_problems_by_user,
    update_problem,
)
from app.services.reaction import compute_reaction_balance, get_user_reaction
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/problems", tags=["problems"])


def get_problem_or_404(problem_id: str, db: Session = Depends(get_db)) -> Problem:
    """
    Вспомогательная функция для @authorize, чтобы получать объект Problem через depends
    """
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem can't be found"
        )
    return problem


@router.post("/solved/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def mark_problem_as_solved_endpoint(
    problem_id: str,
    user_id: str = Query(..., description="ID пользователя, который решил задачу"),
    db: Session = Depends(get_db),
) -> None:
    """
    Помечает задачу как решённую для указанного пользователя
    Добавляет запись в таблицу solved_problems

    Args:
        problem_id (str): идентификатор задачи
        user_id (str): User.keycloak_id пользователя, который решил задачу
        db (Session): сессия для работы с базой данных

    Returns:
        HTTP 204 No Content при успешном выполнении.

    Raises:
        HTTPException 404: если пользователь или задача не найдены.
    """
    user = get_user(db, user_id)

    problem = get_problem(db, problem_id)
    if problem in user.solved_problems:
        return

    user.solved_problems.append(problem)
    db.commit()
    return


@router.post("/", response_model=ProblemRead)
def create_problem_endpoint(
    problem_in: ProblemCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Создает новую задачу, используя данные, полученные от пользователя.

    Args:
        problem_in (ProblemCreate): данные для создания задачи
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        ProblemRead - созданная задача
    """
    problem = create_problem(db, problem_in, creator_id=user_claims.get("sub"))
    return problem


@router.get("/enriched", response_model=list[ProblemReadExtended])
def list_enriched_problems_endpoint(
    offset: int = Query(0, ge=0, description="Смещение для выборки"),
    limit: int = Query(10, ge=1, description="Количество задач на страницу"),
    difficulty: str | None = Query(
        None, description="Фильтр по сложности (EASY, MEDIUM, HARD)"
    ),
    tag_id: str | None = Query(None, description="Фильтр по идентификатору тега"),
    sort_by_rating: bool = Query(False, description="Сортировать по рейтингу"),
    sort_order: str = Query(
        "desc", description="Направление сортировки: 'asc' или 'desc'"
    ),
    db: Session = Depends(get_db),
):
    """
    Возвращает список задач (ProblemReadExtended)
    Пагинация реализована через параметры offset и limit
    Дополнительно можно фильтровать задачи по сложности и тегу, сортировать по рейтингу

    Args:
        offset (int): смещение для выборки (по умолчанию 0)
        limit (int): максимальное число задач на страницу (по умолчанию 10)
        difficulty (optional, str): фильтр по сложности ("EASY", "MEDIUM", "HARD")
        tag_id (optional, str): фильтр по идентификатору тега
        sort_by_rating (bool): если True, сортирует задачи по рейтингу (reaction_balance)
        sort_order (str): направление сортировки ("asc", "desc")
        db (Session): сессия для работы с базой данных

    Returns:
        List[ProblemReadExtended]: список задач.
    """
    enriched_problems = list_enriched_problems_filtered(
        db, offset, limit, difficulty, tag_id, sort_by_rating, sort_order
    )
    return enriched_problems


@router.get("/{problem_id}", response_model=ProblemReadWithReaction)
def read_problem_with_reaction_endpoint(
    problem_id: str,
    db: Session = Depends(get_db),
    user_id: str | None = Query(
        None,
        description="Опционально, ID пользователя для получения его реакции на задачу",
    ),
):
    """
    Возвращает информацию о задаче в виде ProblemReadWithReaction

    Args:
        problem_id (str): идентификатор задачи
        db (Session): сессия для работы с базой данных
        user_id (str, optional): User.keycloak_ID пользователя для поиска его реакции

    Returns:
        ProblemReadWithReaction: объект задачи

    Raises:
        HTTPException: 404, если задача не найдена
    """
    problem = get_problem_or_404(problem_id, db)

    user_obj = get_user(db, problem.created_by)
    author_display_name = user_obj.display_name if user_obj else None

    reaction_balance = compute_reaction_balance(db, problem_id, "problem")

    user_reaction = None
    if user_id:
        reaction = get_user_reaction(db, problem_id, "problem", user_id)
        if reaction:
            user_reaction = reaction.reaction_type

    response = ProblemReadWithReaction.from_orm(problem)
    response.author_display_name = author_display_name
    response.reaction_balance = reaction_balance
    response.user_reaction = user_reaction
    return response


@router.put("/{problem_id}", response_model=ProblemRead)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def update_problem_endpoint(
    update_data: dict,
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет данные задачи и возвращает обновленный объект задачи

    Args:
        update_data (dict): словарь с данными для обновления задачи
        problem (Problem): объект задачи, полученный из БД
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        ProblemRead - обновленная задача

    Raises:
        HTTPException 404 - если задача не найдена
    """
    updated_problem = update_problem(db, problem, update_data)
    return updated_problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def delete_problem_endpoint(
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Удаляет запись задачи

    Args:
        problem (Problem): объект задачи для удаления
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        None - функция ничего не возвращает

    Raises:
        HTTPException 404 - если задача не найдена
    """
    delete_problem(db, problem)
    return


@router.post("/{problem_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def attach_tag_to_problem(
    tag_id: UUID,
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Прикрепляет тег к задаче

    Args:
        tag_id (UUID): идентификатор тега, который требуется прикрепить
        problem (Problem): объект задачи, полученный из БД
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        None - функция ничего не возвращает

    Raises:
        HTTPException 404 - если тег не найден
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    problem.tags.append(tag)
    db.commit()
    return None


@router.delete("/{problem_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def detach_tag_from_problem(
    tag_id: UUID,
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Открепляет тег от задачи

    Args:
        tag_id (UUID): идентификатор тега для отсоединения
        problem (Problem): объект задачи, полученный из БД
        db (Session): объект сессии БД
        user_claims (dict): данные пользователя из токена авторизации

    Returns:
        None - функция ничего не возвращает

    Raises:
        HTTPException 404 - если тег не найден
    """
    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    problem.tags.remove(tag)
    db.commit()
    return None


@router.get("/", response_model=list[ProblemRead])
def list_problems_endpoint(db: Session = Depends(get_db)):
    """
    Возвращает список всех задач

    Args:
        db (Session): объект сессии БД

    Returns:
        list[ProblemRead] - список задач
    """
    problems = list_problems(db)
    return problems


@router.get("/by-tag/{tag_id}", response_model=list[ProblemRead])
def list_problems_by_tag_endpoint(tag_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список задач, связанных с указанным тегом

    Args:
        tag_id (str): идентификатор тега
        db (Session): объект сессии БД

    Returns:
        list[ProblemRead] - список задач с заданным тегом
    """
    problems = list_problems_by_tag(db, tag_id)
    return problems


@router.get("/by-user/{user_id}", response_model=list[ProblemRead])
def list_problems_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список задач, созданных указанным пользователем

    Args:
        user_id (str): идентификатор пользователя (Keycloak ID)
        db (Session): объект сессии БД

    Returns:
        list[ProblemRead] - список задач, созданных пользователем

    Raises:
        HTTPException 404 - если пользователь не найден
    """
    local_user = get_user_or_404(user_id, db)
    problems = list_problems_by_user(db, local_user.keycloak_id)
    return problems


@router.get("/by-difficulty/{difficulty}", response_model=list[ProblemRead])
def list_problems_by_difficulty_endpoint(
    difficulty: str, db: Session = Depends(get_db)
):
    """
    Возвращает список задач заданной сложности.

    Args:
        difficulty (str): уровень сложности задачи (например, "EASY", "MEDIUM", "HARD")
        db (Session): объект сессии БД

    Returns:
        list[ProblemRead] - список задач с указанной сложностью
    """
    problems = list_problems_by_difficulty(db, difficulty)
    return problems
