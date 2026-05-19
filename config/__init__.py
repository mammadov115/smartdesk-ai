# Ensure the Celery app is loaded when Django starts so @shared_task works.
from .celery_app import app as celery_app  # noqa: F401

__all__ = ["celery_app"]
