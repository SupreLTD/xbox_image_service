from celery import Celery
from app.core.config import settings

celery = Celery('task')

celery.conf.broker_url = settings.CELERY_BROKER_URL


class CeleryConfig:
    task_serializer = "pickle"
    result_serializer = "pickle"
    event_serializer = "json"
    accept_content = ["application/json", "application/x-python-serialize"]
    result_accept_content = ["application/json", "application/x-python-serialize"]


celery.config_from_object(CeleryConfig)

celery.conf.result_backend = settings.CELERY_RESULT_BACKEND
celery.autodiscover_tasks(['app.tasks'])
