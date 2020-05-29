#!/usr/bin/env bash
# custom initialisation tasks
# ref - https://docs.cloudfoundry.org/devguide/deploy-apps/deploy-app.html

echo "---- RUNNING release tasks (.profile) ------"

echo "---- Apply Migrations ------"
python manage.py migrate

echo "---- FINISHED release tasks (.profile) ------"
