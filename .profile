#!/usr/bin/env bash
# custom initialisation tasks
# ref - https://docs.cloudfoundry.org/devguide/deploy-apps/deploy-app.html

echo "---- RUNNING release tasks (.profile) ------"

echo "---- Installing Related Barrier ML Packages ------"
mkdir ~/ml-tmp-dir
TMPDIR=~/ml-tmp-dir pip3 install -r requirements-related-barriers.txt

echo "---- Collecting static ------"
python manage.py collectstatic --noinput

echo "---- Apply Migrations ------"
python manage.py migrate

echo "---- FINISHED release tasks (.profile) ------"
