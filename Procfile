web: gunicorn --worker-class=gevent --worker-connections=1000 config.wsgi:application --bind 0.0.0.0:$PORT --log-file -
celeryworker: celery worker -A config.celery -l info -Q celery
celerybeat: celery beat -A config.celery -l info -S django
