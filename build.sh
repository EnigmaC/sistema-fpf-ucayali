#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Cambia --no-input por --verbosity 2 para ver el detalle completo
python manage.py collectstatic --no-input --verbosity 2

python manage.py migrate