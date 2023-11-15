web: mkdir ~/ml-tmp-dir && TMPDIR=~/ml-tmp-dir pip install -r requirements-related-barriers.txt && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --worker-class gevent --worker-connections 1000 --timeout 120 --log-file -
celeryworker: celery -A config.celery worker -l info -Q celery
celerybeat: celery -A config.celery beat -l info -S django
