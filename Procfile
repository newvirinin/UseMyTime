web: cd UseMyTime && python manage.py collectstatic --no-input && python manage.py migrate && gunicorn --bind 0.0.0.0:$PORT wsgi:application
