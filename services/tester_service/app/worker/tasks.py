from app.worker.celery_app import celery_app
from app.services.solution import process_solution
from app.core.logger import logger

@celery_app.task(name="process_solution_task")
def process_solution_task(solution_id: str) -> None:
    logger.info(f"Worker got solution_id={solution_id}")
    process_solution(solution_id)
