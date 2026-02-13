#!/bin/bash
echo "Setting DJANGO_SETTINGS_MODULE to UseMyTime.settings"
export DJANGO_SETTINGS_MODULE=UseMyTime.settings
echo "DJANGO_SETTINGS_MODULE is now: $DJANGO_SETTINGS_MODULE"
echo "Starting gunicorn..."
exec gunicorn UseMyTime.wsgi:application --bind 0.0.0.0:$PORT
