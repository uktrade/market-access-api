web: python manage.py migrate && waitress-serve --port=$PORT config.wsgi:application
celeryworker: celery worker -A config.celery -l info -Q celery
