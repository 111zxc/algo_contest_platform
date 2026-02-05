import os
from celery import Celery

BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")

celery_app = Celery(
    "tester_worker",
    broker=BROKER_URL,
)

celery_app.conf.update(
    task_ignore_result=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
)

celery_app.autodiscover_tasks(["app.worker"])
