web: python manage.py migrate --noinput && opentelemetry-instrument gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker-class gevent --worker-connections 16 --timeout 240 --log-file -
celeryworker: celery -A config.celery worker -l info -Q celery
celerybeat: celery -A config.celery beat -l info -S django
