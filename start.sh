#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python UseMyTime/manage.py collectstatic --no-input

# Apply database migrations
python UseMyTime/manage.py migrate

# Start gunicorn
cd UseMyTime
gunicorn --bind 0.0.0.0:$PORT wsgi:application
