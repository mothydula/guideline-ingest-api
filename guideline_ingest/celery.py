"""
Celery configuration for the guideline ingest project.
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guideline_ingest.settings')

app = Celery('guideline_ingest')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure task routing and execution
""" app.conf.update(
    task_routes={
        'jobs.tasks.process_guideline_task': {'queue': 'guideline_processing'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
) """

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')