"""Celery configuration for async task processing."""

from celery import Celery
from src.core.config import settings

celery_app = Celery("ai_consultancy")

celery_app.conf.broker_url = settings.redis_url
celery_app.conf.result_backend = settings.redis_url
celery_app.conf.task_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.result_serializer = "json"
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True
celery_app.conf.task_track_started = True
celery_app.conf.task_time_limit = 30 * 60
celery_app.conf.task_soft_time_limit = 25 * 60
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_max_tasks_per_child = 1000
celery_app.conf.beat_scheduler = 'redbeat.RedBeatScheduler'
celery_app.conf.beat_max_loop_interval = 300
celery_app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'src.agents.tasks.cleanup_old_tasks',
        'schedule': 86400.0,
        'options': {'expires': 3600}
    },
    'update-agent-memory': {
        'task': 'src.agents.tasks.update_agent_memory',
        'schedule': 3600.0,
        'options': {'expires': 1800}
    },
    'generate-usage-analytics': {
        'task': 'src.agents.tasks.generate_usage_analytics',
        'schedule': 3600.0,
        'options': {'expires': 1800}
    },
}

celery_app.autodiscover_tasks([
    "src.agents"
])
