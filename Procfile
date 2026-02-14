web: cd UseMyTime && python manage.py collectstatic --no-input && python manage.py migrate && python load_initial_data.py && gunicorn --bind 0.0.0.0:$PORT wsgi:application
