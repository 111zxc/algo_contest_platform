from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.solution import Solution, SolutionStatus


def compute_performance_percentile(
    db: Session, problem_id: str, current_time: float
) -> float:
    """
    Возвращает процент решений, которые выполняются медленнее текущего.
    Если других одобренных решений нет, возвращает 100.0

    Args:
        db (Session): объект БД
        problem_id (str): id задачи
        current_time (float): время выполнения данного решения

    Returns:
        float: процент "быстрее, чем N% решений"
    """
    # Всего засчитанных решений к задаче
    total = (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id, Solution.status == SolutionStatus.AC)
        .count()
    )

    # Если это первое засчитанное решение, то быстрее чем 100%
    if total == 0:
        logger.debug(f"No accepted solutions found for {problem_id}. Returning 100.0")
        return 100.0

    # Количество решений, медленнее чем данное
    slower = (
        db.query(Solution)
        .filter(
            Solution.problem_id == problem_id,
            Solution.status == SolutionStatus.AC,
            Solution.time_used > current_time,
        )
        .count()
    )

    # Процент решений медленнее
    percentile = (slower / total) * 100
    logger.info(
        f"Succesfully computed performance for problem with id: {problem_id} with time: {current_time}: {percentile}"
    )
    return percentile
