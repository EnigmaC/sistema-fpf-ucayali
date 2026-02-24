#!/usr/bin/env bash
# Salir si hay errores
set -o errexit

# 1. Instalar librerías
pip install -r requirements.txt

# 2. Recolectar archivos estáticos (CSS, JS, Imágenes)
python manage.py collectstatic --no-input

# 3. Crear las tablas en la base de datos
python manage.py migrate