# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sistema de Gestión Documental (Mesa de Partes Virtual) for the Federación Peruana de Fútbol - Departamental Ucayali. A Django 5.1 web app deployed on Render.

## Development Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Run tests
python manage.py test gestion

# Collect static files
python manage.py collectstatic --no-input --clear

# Create superuser
python manage.py createsuperuser
```

## Required Environment Variables

Create a `.env` file in the project root with:

```
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=          # Optional: PostgreSQL URL (overrides SQLite)
CLOUD_NAME=            # Cloudinary
API_KEY=               # Cloudinary
API_SECRET=            # Cloudinary
EMAIL_HOST_USER=       # Gmail address
EMAIL_HOST_PASSWORD=   # Gmail app password
```

## Architecture

Single Django app (`gestion`) with a `core` config package.

**Data flow:**
- Public users submit documents via `/mesa-virtual/` → `DocumentoForm` validates → saved to DB + file uploaded to Cloudinary → confirmation email sent
- Staff logs in at `/` (custom `sign_in` view) → dashboard at `/dashboard/` → manages expedientes at `/expedientes/`
- State changes (`cambiar_estado`) trigger email notifications to the document submitter
- PDF cargo generation (`generar_cargo`) uses `xhtml2pdf` and embeds a QR code linking to the public tracking page

**Key model — `Documento`:**
- Auto-generates `numero_expediente` in format `EXP-{YEAR}-{NNNN}` on first save
- Files stored on Cloudinary via `CloudinaryField` (folder: `tramites_fpf_ucayali`)
- States: `REC` → `REV` → `DER` / `OBS` → `FIN`

**Storage:**
- Static files: WhiteNoise (`STATICFILES_STORAGE = CompressedStaticFilesStorage`)
- Media files: Cloudinary (`DEFAULT_FILE_STORAGE = MediaCloudinaryStorage`)
- Database: SQLite locally, PostgreSQL on Render via `DATABASE_URL`

**Admin panel:** Accessible at `/sistema-interno-fpf/` (obfuscated path), styled with django-jazzmin.

## Deployment (Render)

`build.sh` runs on deploy:
```bash
pip install -r requirements.txt
python manage.py collectstatic --no-input --clear
python manage.py migrate
```

Production security settings (SSL redirect, secure cookies, CSRF trusted origins for `*.onrender.com`) activate automatically when `DEBUG=False`.
