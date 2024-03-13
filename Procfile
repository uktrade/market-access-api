web: python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker-class gevent --worker-connections 1000 --timeout 120 --log-file -
celeryworker: TEST_ENV_VAR=True celery -A config.celery worker -l info -Q celery
celerybeat: celery -A config.celery beat -l info -S django
