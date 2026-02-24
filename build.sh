#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# --clear fuerza borrar y recopiar todo desde cero
python manage.py collectstatic --no-input --clear

python manage.py migrate