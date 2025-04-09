from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.solution import Solution, SolutionStatus


def compute_performance_percentile(
    db: Session, problem_id: str, current_time: float
) -> float:
    """
    Вычисляет процентиль текущего решения по времени выполнения среди всех решений с статусом AC для данной задачи.

    Возвращает процент решений, которые выполняются медленнее текущего.
    Если решений нет, возвращает 100 (т.е. текущее решение – самое быстрое).
    """
    total = (
        db.query(Solution)
        .filter(Solution.problem_id == problem_id, Solution.status == SolutionStatus.AC)
        .count()
    )

    if total == 0:
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
    logger.info(
        f"Succesfully computed performance for problem with id: {problem_id} with time: {current_time}: {percentile}"
    )
    return percentile
