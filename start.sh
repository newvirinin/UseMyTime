#!/bin/bash
export DJANGO_SETTINGS_MODULE=UseMyTime.settings
exec gunicorn UseMyTime.wsgi:application --bind 0.0.0.0:$PORT
