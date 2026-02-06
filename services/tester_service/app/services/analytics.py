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
        db (Session): объект сессии БД
        problem_id (str): id задачи
        current_time (float): время выполнения данного решения

    Returns:
        float: процент "быстрее, чем N% решений"
    """
    total = (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id, Solution.status == SolutionStatus.AC)
        .count()
    )

    if total == 0:
        logger.debug("analytics_compute", extra={'problem_id': problem_id, 'detail': 'first solution'})
        return 100.0

    slower = (
        db.query(Solution)
        .filter(
            Solution.problem_id == problem_id,
            Solution.status == SolutionStatus.AC,
            Solution.time_used > current_time,
        )
        .count()
    )

    percentile = (slower / total) * 100
    logger.debug('analytics_compute', extra={'problem_id': problem_id, 'time': current_time, 'percentile': percentile})
    return percentile
