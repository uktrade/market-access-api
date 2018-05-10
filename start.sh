#!/bin/bash -xe
set -euo pipefail
IFS=$'\n\t'

cd /app

echo "Apply database migrations"
python manage.py migrate --noinput

echo "Starting Gunicorn"
gunicorn -c gunicorn/conf.py config.wsgi --log-file - --access-logfile - --workers=$(nproc --all) --bind=0.0.0.0 --timeout=55 --log-level=debug --capture-output
