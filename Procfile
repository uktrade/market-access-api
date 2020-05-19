web: python manage.py migrate && gunicorn --worker-class=gevent --worker-connections=1000 --workers 9 config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
celeryworker: celery worker -A config.celery -l info -Q celery
celerybeat: celery beat -A config.celery -l info
