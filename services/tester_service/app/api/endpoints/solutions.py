from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.solution import SolutionCreate, SolutionRead
from app.services.solution import (
    create_solution,
    get_solution,
    list_contest_solutions,
    list_solutions_by_problem,
    list_solutions_by_problem_and_user,
    process_solution,
)

router = APIRouter(prefix="/solutions", tags=["solutions"])


@router.post(
    "/",
    response_model=SolutionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить решение",
    description="Отправить новое решение к указанной задаче"
    "Решение будет обработано на фоне, но сервер вернет ответ "
    "сразу после получения запроса.",
)
def submit_solution(
    solution_in: SolutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
) -> SolutionRead:
    """
    Отправить новое решение на проверку к указанной проблеме

    Args:
        solution_in (SolutionCreate): данные о создаваемом решении
        background_tasks (BackgroundTasks): менеджер фоновых задач
        db (Session): сессия к БД
        user_claims (dict): данные о пользователе из токена авторизации

    Returns:
        SolutionRead: созданное решение
    """
    user_id = user_claims.get("sub")
    solution = create_solution(db, solution_in, user_id)

    background_tasks.add_task(process_solution, str(solution.id))

    return solution


@router.get(
    "/{contest_id}/solutions",
    response_model=list[SolutionRead],
    status_code=status.HTTP_200_OK,
)
def list_solutions_endpoint(
    contest_id: str,
    user_claims: dict = Depends(get_current_user),
    user_id: str | None = Query(
        None, description="Опциональный Keycloak ID участника для фильтра"
    ),
    problem_id: str | None = Query(
        None, description="Опциональный ID задачи для фильтра"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, description="Размер страницы"),
    db: Session = Depends(get_db),
):
    owner_id = user_claims["sub"]
    return list_contest_solutions(
        db,
        contest_id=str(contest_id),
        owner_id=owner_id,
        user_id=user_id,
        problem_id=problem_id,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{solution_id}",
    response_model=SolutionRead,
    status_code=status.HTTP_200_OK,
    summary="Получить данные о решении",
    description="Получить данные о решении согласно схеме SolutionRead",
)
def get_solution_status(
    solution_id: UUID,
    db: Session = Depends(get_db),
) -> SolutionRead:
    """
    Возвращает актуальный статус решения по его идентификатору.
    Перед возвратом пересчитывает показатель производительности (faster_than)
    для принятых решений, используя время выполнения.

    Args:
        solution_id (UUID): идентификатор решения
        db (Session): сессия к БД

    Returns:
        SolutionRead: данные о решении

    Raises:
        HTTPException: 404, если решение не найдено
    """
    solution = get_solution(db, str(solution_id))
    if not solution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found"
        )
    return solution


@router.get(
    "/by-problem/{problem_id}",
    response_model=list[SolutionRead],
    summary="Получить данные о всех решениях к проблеме",
)
def list_solutions_by_problem_endpoint(
    problem_id: str, db: Session = Depends(get_db)
) -> list[SolutionRead]:
    """
    Возвращает список решений к задаче problem_id

    Args:
        problem_id: идентификатор задачи
        db: объект к БД

    Returns:
        list[SolutionRead]: список решений, отправленных к задаче problem_id
    """
    solutions = list_solutions_by_problem(db, problem_id)
    return solutions


@router.get(
    "/my/{problem_id}",
    response_model=list[SolutionRead],
    summary="Получить список решений задачи пользователем",
    description="Позволяет получить список всех решений к данной задаче пользователем, "
    "определяемым по его токену авторизации.",
)
def list_my_solutions_for_problem_endpoint(
    problem_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
) -> list[SolutionRead]:
    """
    Возвращает список решений, отправленных текущим пользователем к задаче problem_id

    Args:
        problem_id: идентификатор задачи
        db: объект к БД
        user_claims: информация о текущем пользователе

    Returns:
        list[SolutionRead]: список решений, отправленных к задаче problem_id
    """
    keycloak_id = user_claims.get("sub")
    solutions = list_solutions_by_problem_and_user(db, problem_id, keycloak_id)
    return solutions
