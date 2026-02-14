#!/bin/bash

echo "Starting UseMyTime deployment..."
echo ""

# Check configuration
echo "Checking configuration..."
python check_railway_config.py
if [ $? -ne 0 ]; then
    echo "❌ Configuration check failed!"
    exit 1
fi
echo ""

# Collect static files
echo "Collecting static files..."
python UseMyTime/manage.py collectstatic --no-input
echo ""

# Run migrations
echo "Running migrations..."
python UseMyTime/manage.py migrate --no-input
echo ""

# Start Gunicorn
echo "Starting Gunicorn..."
echo "Binding to 0.0.0.0:$PORT"
gunicorn --chdir UseMyTime --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile - wsgi:application
