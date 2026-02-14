#!/usr/bin/env bash
set -e

cd UseMyTime

echo "Loading data from backup..."
if python manage.py loaddata ../data_backup.json --ignorenonexistent; then
    echo "Data loaded successfully!"
else
    echo "Warning: Data loading failed or partially completed"
fi
