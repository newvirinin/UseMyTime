"""
WSGI config for UseMyTime project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Force the settings module to override any environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'UseMyTime.settings'

# Debug print to verify the settings module (will appear in logs)
print(f"DJANGO_SETTINGS_MODULE is set to: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

application = get_wsgi_application()
