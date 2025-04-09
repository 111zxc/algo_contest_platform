import requests

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logger import logger
from app.models.solution import Solution, SolutionStatus
from app.schemas.solution import SolutionCreate
from app.services.analytics import compute_performance_percentile
from app.services.docker_runner import run_solution_in_container


def create_solution(db, solution_in: SolutionCreate, user_id: str) -> Solution:
    """
    Создает новое решение со статусом PENDING и сохраняет его в БД.
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
    logger.info(
        f"Succesfully created solution {solution.id} to problem with id: {solution_in.problem_id} by user with id: {user_id}"
    )
    return solution


def get_solution(db, solution_id: str) -> Solution | None:
    """
    Возвращает решение по его идентификатору или None, если не найдено.
    """
    result = db.query(Solution).filter(Solution.id == solution_id).first()
    if result is None:
        logger.info(f"Couldn't get solution by id: {solution_id}")
    else:
        logger.info(f"Succesfully got solution with id {solution_id}")
    return result


def update_solution_status(db, solution_id: str, result: dict) -> Solution | None:
    """
    Обновляет статус решения, время, память и сравнительную статистику в БД.
    """
    solution = get_solution(db, solution_id)
    if solution is None:
        return None
    solution.status = result.get("status", SolutionStatus.RE)
    solution.time_used = result.get("time_used")
    solution.memory_used = result.get("memory_used")
    solution.faster_than = result.get("faster_than")
    db.commit()
    db.refresh(solution)
    logger.info(f"Succesfully updated solution status with id {solution_id}")
    return solution


def process_solution(solution_id: str):
    """
    Фоновая функция для обработки решения:
    1. Получает данные задачи с content_service (тесткейсы, лимиты).
    2. Запускает выполнение решения для каждого тесткейса через run_solution_in_container.
    3. Композитно определяет общий статус.
    4. Обновляет запись решения в БД.
    """
    db = SessionLocal()
    try:
        solution = get_solution(db, solution_id)
        if not solution:
            return {"error": "Solution not found"}

        problem_url = f"{settings.CONTENT_SERVICE_URL}/problems/{solution.problem_id}"
        response = requests.get(problem_url)
        if response.status_code != 200:
            update_solution_status(
                db, solution_id, {"status": SolutionStatus.RE, "time_used": 0}
            )
            logger.info(f"Couldn't process solution {solution_id}: Problem not found")
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
        time_limit = problem_data.get("time_limit", 2000) / 1000.0

        result = run_solution_in_container(
            solution.code, solution.language, test_cases, time_limit
        )
        logger.info(f"Started processing solution {solution_id}'s code")

        if result.get("status") == "AC" and result.get("results"):
            current_time = result["results"][0]["time_used"]

            percentile = compute_performance_percentile(
                db, solution.problem_id, current_time
            )
            result["faster_than"] = percentile
        else:
            result["faster_than"] = None

        update_solution_status(db, solution_id, result)
        logger.info(
            f"Succesfully updated solution {solution_id}'s status to {result.get("status")}"
        )
        return result
    finally:
        db.close()


def list_solutions_by_problem(db, problem_id: str) -> list[Solution]:
    """
    Возвращает список всех решений для заданной задачи.
    """
    logger.info(f"Got all solutions to problem {problem_id}")
    return db.query(Solution).filter(Solution.problem_id == problem_id).all()


def list_solutions_by_problem_and_user(
    db, problem_id: str, keycloak_id: str
) -> list[Solution]:
    """
    Возвращает список решений для заданной задачи, оставленных пользователем с указанным keycloak_id.
    """
    logger.info(f"Got all solutions to problem {problem_id} from user {keycloak_id}")
    return (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id, Solution.user_id == keycloak_id)
        .all()
    )
