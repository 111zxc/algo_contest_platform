from sqlalchemy.orm import Session, joinedload

from app.core.logger import logger
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
    logger.info(f"Succesfully created problem with id: {problem.id}")
    return problem


def get_problem(db: Session, problem_id: str) -> Problem | None:
    result = (
        db.query(Problem)
        .filter(Problem.id == problem_id)
        .options(joinedload(Problem.tags))
        .first()
    )
    if result is None:
        logger.info(f"Couldn't get problem by id: {problem_id}")
    else:
        logger.info(f"Succesfully got problem with id: {problem_id}")
    return result


def update_problem(db: Session, problem: Problem, update_data: dict) -> Problem:
    for key, value in update_data.items():
        setattr(problem, key, value)
    db.commit()
    db.refresh(problem)
    logger.info(f"Succesfully updated problem with id: {problem.id}")
    return problem


def delete_problem(db: Session, problem: Problem) -> None:
    db.delete(problem)
    logger.info(f"Succesfully deleted problem with id: {problem.id}")
    db.commit()


def list_problems(db: Session) -> list[Problem]:
    logger.info("Succesfully listed all problems")
    return db.query(Problem).options(joinedload(Problem.tags)).all()


def list_problems_by_tag(db: Session, tag_id: str) -> list[Problem]:
    logger.info(f"Succesfully listed all problems by tag {tag_id}")
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.tags.any(id=tag_id))
        .all()
    )


def list_problems_by_user(db: Session, user_id: str) -> list[Problem]:
    logger.info(f"Succesfully listed all problems by user {user_id}")
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.created_by == user_id)
        .all()
    )


def list_problems_by_difficulty(db: Session, difficulty: str) -> list[Problem]:
    logger.info(f"Succesfully listed all problems by difficulty: {difficulty}")
    return (
        db.query(Problem)
        .options(joinedload(Problem.tags))
        .filter(Problem.difficulty == difficulty)
        .all()
    )
