web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker-class gevent --worker-connections 1000 --timeout 120 --log-file -
celeryworker: celery worker -A config.celery -l info -Q celery
celerybeat: celery beat -A config.celery -l info -S django
