web: python manage.py migrate && gunicorn --worker-class=gevent --worker-connections=1000 --workers 9 config.wsgi:application --bind 0.0.0.0:$PORT --timeout 60
celeryworker: celery worker -A config.celery -l info -Q celery
