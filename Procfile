web: python UseMyTime/manage.py collectstatic --no-input && python UseMyTime/manage.py migrate && cd UseMyTime && gunicorn --bind 0.0.0.0:$PORT wsgi:application
