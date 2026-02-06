import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.models.solution import Solution, SolutionStatus
from app.schemas.solution import SolutionCreate
from app.services.analytics import compute_performance_percentile
from app.services.docker_runner import run_solution_in_container


def create_solution(db: Session, solution_in: SolutionCreate, user_id: str) -> Solution:
    """
    Создает и  сохраняет в БД запись решения со статусом pending

    Args:
        db: объект сессии БД,
        solution_in (SolutionCreate): заполненная схема для создания решения,
        user_id (str): str(user.keycloak_id)

    Returns:
        Solution: orm объект решения
    """
    solution = Solution(
        created_by=user_id,
        problem_id=solution_in.problem_id,
        code=solution_in.code,
        language=solution_in.language,
        status=SolutionStatus.PENDING,
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    logger.debug("solution_create", extra={"created_by": user_id, "problem_id": str(solution_in.problem_id)})
    return solution


def get_solution(db: Session, solution_id: str) -> Solution | None:
    """
    Возвращает orm объект решения по его id

    Args:
        db (Session): объект сессии БД,
        solution_id (str): id решения,

    Returns:
        Solution | None: orm объект решения или None
    """
    solution = db.query(Solution).filter(Solution.id == solution_id).first()
    if not solution:
        logger.warning("solution_get_notfound", extra={'solution_id': solution_id})
    else:
        logger.debug("solution_get", extra={'solution_id': solution_id})
    return solution


def update_solution_status(
    db: Session, solution_id: str, result: dict
) -> Solution | None:
    """
    Обновляет запись решения после его обработки

    Args:
        db (Session): объект сессии БД,
        solution_id (str): id решения,
        result (dict): словарь с результатами обработки решения {status, time_used, memory_used, faster_than}

    Returns:
        Solution | None: orm объект обновленного решения
    """
    solution = get_solution(db, solution_id)
    if solution is None:
        return None

    solution.status = result.get("status", SolutionStatus.RE)
    solution.time_used = result.get("time_used")
    solution.memory_used = result.get("memory_used")
    solution.faster_than = result.get("faster_than")

    try:
        db.commit()
        db.refresh(solution)
        logger.debug("solution_updatestatus", extra={'solution_id': solution_id, 'status': result['status']})
    except Exception:
        db.rollback()
        logger.exception("solution_updatestatus_failed", extra={'solution_id': solution_id})
        return None

    return solution


def process_solution(solution_id: str) -> dict:
    """
    Background функция для обработки пользовательского решения:
    1. Получает тест-кейсы, лимит задачи от solution.problem_id
    2. Запускает решение на тест-кейсах задачи через docker_runner/run_solution_in_container
    3. Выставляет вердикт решению
    4. Обновляет запись решения

    Args:
        db (Session): сессия БД,
        solution_id (str): id решения,

    Returns:
        dict: результат обработки решения {status, faster_than, memory_used, time_used}
    """
    db = SessionLocal()
    try:
        solution = get_solution(db, solution_id)
        if not solution:
            update_solution_status(
                db, solution_id, {"status": SolutionStatus.RE, "time_used": 0}
            )
            return {"error": "Solution not found"}

        problem_url = f"{settings.CONTENT_SERVICE_URL}/problems/{solution.problem_id}"
        response = requests.get(problem_url)
        if response.status_code != 200:
            update_solution_status(
                db, solution_id, {"status": SolutionStatus.RE, "time_used": 0}
            )
            return {"error": "Problem not found"}

        problem_data = response.json()
        test_cases_raw = problem_data.get("test_cases", [])
        test_cases = []
        for tc in test_cases_raw:
            test_cases.append(
                {
                    "input": tc.get("input_data", ""),
                    "expected_output": tc.get("output_data", ""),
                }
            )
        time_limit = problem_data.get("time_limit", 10)
        memory_limit = problem_data.get("memory_limit", 128)

        result = run_solution_in_container(
            solution.code, solution.language, test_cases, time_limit, memory_limit
        )

        if result.get("status") == "AC" and result.get("results"):
            mark_url = (
                f"{settings.CONTENT_SERVICE_URL}/problems/solved/{solution.problem_id}"
            )
            params = {"user_id": solution.created_by}
            try:
                resp = requests.post(mark_url, params=params)
                if not resp.ok:
                    logger.warning("solution_process_warning",
                                   extra={'detail': 'marking solution as solved failed'})
            except Exception:
                logger.exception("solution_process_failed",
                                 extra={"detail": 'post failed for marking problem solved',
                                        'solution_id': solution_id})

            current_time = result["results"][0]["time_used"]
            percentile = compute_performance_percentile(
                db, solution.problem_id, current_time
            )
            result["faster_than"] = percentile
        else:
            result["faster_than"] = None

        updated_solution = update_solution_status(db, solution_id, result)
        if updated_solution:
            logger.debug('solution_process', extra={'solution_id': solution_id})
        else:
            logger.error("solution_process_failed",
                         extra={'detail': 'failed to update status', 'solution_id': solution_id})
        return result

    finally:
        db.close()


def list_solutions_by_problem(db: Session, problem_id: str) -> list[Solution]:
    """
    Возвращает список всех решений к задаче problem_id

    Args:
        db (Session): объект БД,
        problem_id (str): id задачи

    Returns:
        list[Solution]: список пользовательских решений к задаче
    """
    solutions = db.query(Solution).filter(Solution.problem_id == problem_id).all()
    logger.debug("solution_listproblem", extra={'problem_id': problem_id, 'length': len(solutions)})
    return solutions


def list_solutions_by_problem_and_user(
    db, problem_id: str, user_id: str
) -> list[Solution]:
    """
    Возвращает список всех решений пользователя user_id к задаче problem_id

    Args:
        db (Session): объект БД,
        problem_id (str): id проблемы,
        user_id (str): id пользователя

    Returns:
        list[Solution]: список решений пользователя user_id к задаче problem_id
    """
    solutions = (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id, Solution.created_by == user_id)
        .all()
    )
    logger.debug('solution_listproblemuser',
                 extra={"problem_id": problem_id, "user_id": user_id, "length": len(solutions)})
    return solutions


def list_contest_solutions(
    db: Session,
    contest_id: str,
    owner_id: str,
    user_id: str | None = None,
    problem_id: str | None = None,
    offset: int = 0,
    limit: int = 10,
) -> list[Solution]:
    tasks_url = f"{settings.CONTENT_SERVICE_URL}/contests/{contest_id}/tasks"
    try:
        r = requests.get(tasks_url, timeout=5)
        r.raise_for_status()
    except Exception:
        logger.exception("solution_listcontest_failed", extra={'contest_id': contest_id})
        raise
    tasks = r.json()
    task_ids = [str(t["id"]) for t in tasks]

    parts_url = f"{settings.CONTENT_SERVICE_URL}/contests/{contest_id}/participants"
    try:
        r = requests.get(parts_url, timeout=5)
        r.raise_for_status()
    except Exception:
        logger.exception("solution_listcontest_failed",
                         extra={'detail': 'failed to fetch participants for contest',
                                'contest_id': contest_id})
        raise
    participants = r.json()
    participant_ids = [u["keycloak_id"] for u in participants]

    q = db.query(Solution).filter(
        Solution.problem_id.in_(task_ids),
        Solution.created_by.in_(participant_ids),
    )
    if user_id:
        q = q.filter(Solution.created_by == user_id)
    if problem_id:
        q = q.filter(Solution.problem_id == problem_id)

    solutions = q.offset(offset).limit(limit).all()
    logger.debug('solutions_listcontest',
                 extra={'contest_id': contest_id, 'user_id': user_id, 'problem_id': problem_id,
                        'offset': offset, 'limit': limit, 'length': len(solutions)})
    return solutions
