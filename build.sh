#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input --clear
python manage.py migrate

# Crear superusuario automáticamente
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='patricia').exists():
    User.objects.create_superuser('patricia', 'pattytutu190879@gmail.com', '40792145')
    print('Superusuario creado')
"