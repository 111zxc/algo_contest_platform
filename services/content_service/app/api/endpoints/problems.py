from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import authorize, get_current_user, get_db
from app.schemas.problem import ProblemCreate, ProblemRead, ProblemReadExtended
from app.services.problem import (
    create_problem,
    delete_problem,
    get_problem,
    list_problems,
    list_problems_by_difficulty,
    list_problems_by_tag,
    list_problems_by_user,
    update_problem,
    list_enriched_problems
)
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/problems", tags=["problems"])


def get_problem_or_404(problem_id: str, db: Session = Depends(get_db)):
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена"
        )
    return problem


@router.post("/", response_model=ProblemRead)
def create_problem_endpoint(
    problem_in: ProblemCreate,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Для пользовательского создания задач
    """
    problem = create_problem(db, problem_in, creator_id=user_claims.get("sub"))
    return problem


@router.get("/enriched", response_model=list[ProblemReadExtended])
def list_enriched_problems_endpoint(
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
    limit: int = Query(10, ge=1, description="Количество задач на страницу"),
    db: Session = Depends(get_db)
):
    """
    Возвращает список задач с добавленным полем author_display_name (display_name автора) с пагинацией.
    
    Query Parameters:
        - offset: смещение (начальное значение 0)
        - limit: максимальное количество записей (по умолчанию 10)
    
    Returns:
        List[ProblemReadExtended]: Обогащенный список задач.
    """
    enriched = list_enriched_problems(db, offset, limit)
    return enriched


@router.get("/{problem_id}", response_model=ProblemRead)
def read_problem_endpoint(problem_id: str, db: Session = Depends(get_db)):
    """
    Возвращает 200 и schemas.problem.ProblemRead
    или 404, если задача не существует
    """
    return get_problem_or_404(problem_id, db)


@router.put("/{problem_id}", response_model=ProblemRead)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def update_problem_endpoint(
    update_data: dict,
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    updated_problem = update_problem(db, problem, update_data)
    return updated_problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
@authorize(required_role="admin", owner_param="problem", owner_field="created_by")
def delete_problem_endpoint(
    problem: object = Depends(get_problem_or_404),
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
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
    Возвращает список всех задач.
    """
    problems = list_problems(db)
    return problems


@router.get("/by-tag/{tag_id}", response_model=list[ProblemRead])
def list_problems_by_tag_endpoint(tag_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список задач, связанных с указанным тэгом.
    """
    problems = list_problems_by_tag(db, tag_id)
    return problems


@router.get("/by-user/{user_id}", response_model=list[ProblemRead])
def list_problems_by_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """
    Возвращает список задач, созданных указанным пользователем.
    """
    local_user = get_user(db, user_id)
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    problems = list_problems_by_user(db, local_user.keycloak_id)
    return problems


@router.get("/by-difficulty/{difficulty}", response_model=list[ProblemRead])
def list_problems_by_difficulty_endpoint(
    difficulty: str, db: Session = Depends(get_db)
):
    """
    Возвращает список задач заданной сложности.
    """
    problems = list_problems_by_difficulty(db, difficulty)
    return problems
