from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.solution import SolutionCreate, SolutionRead
from app.services.solution import (
    create_solution,
    get_solution,
    list_solutions_by_problem,
    list_solutions_by_problem_and_user,
    process_solution,
)

router = APIRouter(prefix="/solutions", tags=["solutions"])


@router.post("/", response_model=SolutionRead, status_code=status.HTTP_201_CREATED)
def submit_solution(
    solution_in: SolutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Принимает решение от пользователя, сохраняет его со статусом PENDING,
    получает данные задачи из content_service и запускает асинхронную проверку решения.
    """
    user_id = user_claims.get("sub")

    solution = create_solution(db, solution_in, user_id)

    background_tasks.add_task(process_solution, str(solution.id))

    return solution


@router.get("/{solution_id}", response_model=SolutionRead)
def get_solution_status(
    solution_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Возвращает актуальный статус решения по его идентификатору.
    """
    solution = get_solution(db, str(solution_id))
    if not solution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found"
        )
    return solution


@router.get("/by-problem/{problem_id}", response_model=list[SolutionRead])
def list_solutions_by_problem_endpoint(problem_id: str, db: Session = Depends(get_db)):
    """
    Возвращает list[SolutionRead] всех решений для задачи по ее problem_id.
    """
    solutions = list_solutions_by_problem(db, problem_id)
    return solutions


@router.get("/my/{problem_id}", response_model=list[SolutionRead])
def list_my_solutions_for_problem_endpoint(
    problem_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Возвращает список решений для задачи problem_id, принадлежащих текущему пользователю.
    """
    keycloak_id = user_claims.get("sub")
    solutions = list_solutions_by_problem_and_user(db, problem_id, keycloak_id)
    return solutions
