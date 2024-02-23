#!/usr/bin/env bash
# custom initialisation tasks
# ref - https://docs.cloudfoundry.org/devguide/deploy-apps/deploy-app.html

echo "---- RUNNING release tasks (.profile) ------"

echo "---- Installing Related Barrier ML Packages ------"
/tmp/lifecycle/shell
python -m pip install sentence-transformers==2.2.2 --no-deps
python -m pip install pandas==2.0.3 --no-deps
python -m pip install torch==2.0.0 torchvision==0.15.1 --extra-index-url https://download.pytorch.org/whl/cpu

echo "---- Collecting static ------"
python manage.py collectstatic --noinput

echo "---- Apply Migrations ------"
python manage.py migrate

echo "---- FINISHED release tasks (.profile) ------"
