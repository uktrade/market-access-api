web: chmod +x run.sh && ./run.sh
celeryworker: celery -A config.celery worker -l info -Q celery
celerybeat: celery -A config.celery beat -l info -S django
