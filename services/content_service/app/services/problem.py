from sqlalchemy.orm import Session, joinedload

from app.models.problem import Problem
from app.schemas.problem import ProblemCreate


def create_problem(db: Session, problem_in: ProblemCreate, creator_id: str) -> Problem:
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
    )

    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


def get_problem(db: Session, problem_id: str) -> Problem | None:
    return (
        db.query(Problem)
        .filter(Problem.id == problem_id)
        .options(joinedload(Problem.tags))
        .first()
    )


def update_problem(db: Session, problem: Problem, update_data: dict) -> Problem:
    for key, value in update_data.items():
        setattr(problem, key, value)
    db.commit()
    db.refresh(problem)
    return problem


def delete_problem(db: Session, problem: Problem) -> None:
    db.delete(problem)
    db.commit()


def list_problems(db: Session) -> list[Problem]:
    return db.query(Problem).options(joinedload(Problem.tags)).all()


def list_problems_by_tag(db: Session, tag_id: str) -> list[Problem]:
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.tags.any(id=tag_id))
        .all()
    )


def list_problems_by_user(db: Session, user_id: str) -> list[Problem]:
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.created_by == user_id)
        .all()
    )


def list_problems_by_difficulty(db: Session, difficulty: str) -> list[Problem]:
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.difficulty == difficulty)
        .all()
    )
