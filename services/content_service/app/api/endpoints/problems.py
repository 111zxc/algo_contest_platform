from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.problem import ProblemCreate, ProblemRead
from app.services.problem import (
    create_problem,
    delete_problem,
    get_problem,
    list_problems,
    list_problems_by_difficulty,
    list_problems_by_tag,
    list_problems_by_user,
    update_problem,
)
from app.services.tag import get_tag
from app.services.user import get_user

router = APIRouter(prefix="/problems", tags=["problems"])


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


@router.get("/{problem_id}", response_model=ProblemRead)
def read_problem_endpoint(problem_id: str, db: Session = Depends(get_db)):
    """
    Возвращает 200 и schemas.problem.ProblemRead
    или 404, если задача не существует
    """
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )
    return problem


@router.put("/{problem_id}", response_model=ProblemRead)
def update_problem_endpoint(
    problem_id: str,
    update_data: dict,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    Обновляет предоставленные в body json поля задачи
    только admin или автор
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    if problem.created_by != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this problem",
        )

    problem = update_problem(db, problem, update_data)
    return problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem_endpoint(
    problem_id: str,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    удаляет задачу и отдает 204
    404, если задачи не существует
    только admin или автор
    """
    current_keycloak_id = user_claims.get("sub")
    roles = user_claims.get("realm_access", {}).get("roles", [])

    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    if problem.created_by != current_keycloak_id and "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this problem",
        )

    delete_problem(db, problem)
    return


@router.post("/{problem_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def attach_tag_to_problem(
    problem_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    прикрепляет тэг к задаче
    404, если задачи или тега не существует
    только admin или автор задачи
    """
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    current_keycloak_id = user_claims.get("sub")
    if problem.created_by != current_keycloak_id and "admin" not in user_claims.get(
        "realm_access", {}
    ).get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this problem",
        )

    tag = get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )

    problem.tags.append(tag)
    db.commit()
    return None


@router.delete("/{problem_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_tag_from_problem(
    problem_id: UUID,
    tag_id: UUID,
    db: Session = Depends(get_db),
    user_claims: dict = Depends(get_current_user),
):
    """
    откепляет тег от задачи
    404, если задачи или тег не найдены
    только admin или автор задачи
    """
    problem = get_problem(db, problem_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    current_keycloak_id = user_claims.get("sub")
    if problem.created_by != current_keycloak_id and "admin" not in user_claims.get(
        "realm_access", {}
    ).get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this problem",
        )

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
