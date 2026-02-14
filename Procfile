web: python UseMyTime/manage.py collectstatic --no-input && python UseMyTime/manage.py migrate && gunicorn --chdir UseMyTime --bind 0.0.0.0:$PORT wsgi:application
