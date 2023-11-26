#!/usr/bin/env bash
# custom initialisation tasks
# ref - https://docs.cloudfoundry.org/devguide/deploy-apps/deploy-app.html

echo "---- RUNNING release tasks (.profile) ------"

echo "---- Installing Related Barrier ML Packages ------"
mkdir ~/ml-tmp-dir
/tmp/lifecycle/shell
python -m pip install sentence-transformers==2.2.2 --no-deps
python -m pip install torch==2.0.0 torchvision==0.15.1 --extra-index-url https://download.pytorch.org/whl/cpu

TMPDIR=~/ml-tmp-dir python -m pip install -r requirements-related-barriers.txt

echo "---- Collecting static ------"
python manage.py collectstatic --noinput

echo "---- Apply Migrations ------"
python manage.py migrate

echo "---- FINISHED release tasks (.profile) ------"
