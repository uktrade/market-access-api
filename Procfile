web: python manage.py migrate && waitress-serve --port=$PORT config.wsgi:application
celeryworker: celery worker -A config -l info -Q celery
