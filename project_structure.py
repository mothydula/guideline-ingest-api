# manage.py
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

if __name__ == '__main__':
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guideline_ingest.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

# guideline_ingest/__init__.py
# This will make sure the app is always imported when Django starts
from .celery import app as celery_app

__all__ = ('celery_app',)

# guideline_ingest/wsgi.py
"""
WSGI config for guideline_ingest project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guideline_ingest.settings')
application = get_wsgi_application()

# jobs/__init__.py
# Empty file to make this directory a Python package

# jobs/admin.py
from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id',)
    readonly_fields = ('id', 'created_at', 'updated_at')

# jobs/apps.py
from django.apps import AppConfig

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'