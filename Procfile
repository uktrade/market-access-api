web: gunicorn --worker-class=gevent --worker-connections=1000 --workers 9 config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
celery_worker: celery worker -A config.celery -l info -Q celery
celery_beat: celery beat -A config.celery -l info -S django
