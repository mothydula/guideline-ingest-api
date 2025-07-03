"""
WSGI config for guideline_ingest project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guideline_ingest.settings')
application = get_wsgi_application()