"""
Django settings for core project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
import dj_database_url  # RECOMENDADO: Para conectar base de datos en la nube (si usas Postgres)

# 1. Definimos la ruta base
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Cargamos variables de entorno
load_dotenv(BASE_DIR / '.env')

# 3. Verificación rápida
if os.getenv('CLOUD_NAME'):
    print(f"✅ Configuración cargada. Cloud: {os.getenv('CLOUD_NAME')}")

SECRET_KEY = os.getenv('SECRET_KEY')

# En producción (Render), DEBUG debe ser False
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS: En Render, tu dominio será algo como 'tu-app.onrender.com'
# El '*' permite todo, útil para evitar errores de dominio al inicio.
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost,*').split(',')


# ===================================================
# APLICACIONES
# ===================================================
INSTALLED_APPS = [
    'jazzmin',                  # Panel Admin (Diseño)
    'cloudinary_storage',       # Adaptador Cloudinary
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary',               # SDK Cloudinary
    'gestion',                  # Tu App
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Vital para Render
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# ===================================================
# BASE DE DATOS
# ===================================================
# NOTA: SQLite en Render se borra cada vez que actualizas la página.
# Para producción real se usa PostgreSQL, pero para probar esto sirve.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Si en el futuro agregas PostgreSQL en Render, este código lo detecta automático:
if os.getenv('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(default=os.getenv('DATABASE_URL'))


# ===================================================
# VALIDACIÓN PASSWORD
# ===================================================
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]


# ===================================================
# IDIOMA Y ZONA
# ===================================================
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True


# ===================================================
# ARCHIVOS ESTÁTICOS (CSS/JS)
# ===================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# USAMOS "CompressedStaticFilesStorage" EN LUGAR DE "Manifest"
# El "Manifest" es muy estricto y si falta un archivo .map o una imagen, rompe el deploy.
# Este es más seguro para empezar.
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'


# ===================================================
# MULTIMEDIA (CLOUDINARY)
# ===================================================
cloudinary.config(
    cloud_name = os.getenv('CLOUD_NAME'),
    api_key = os.getenv('API_KEY'),
    api_secret = os.getenv('API_SECRET'),
    secure = True
)

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUD_NAME'),
    'API_KEY': os.getenv('API_KEY'),
    'API_SECRET': os.getenv('API_SECRET')
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'


# ===================================================
# EMAIL
# ===================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f'Mesa de Partes FPF <{os.getenv("EMAIL_HOST_USER")}>'


# ===================================================
# REDIRECCIONES
# ===================================================
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ===================================================
# JAZZMIN
# ===================================================
JAZZMIN_SETTINGS = {
    "site_title": "Admin FPF Ucayali",
    "site_header": "Gestión FPF",
    "site_brand": "FPF Ucayali",
    "welcome_sign": "Bienvenido al Panel Administrativo FPF",
    "copyright": "Federación Peruana de Fútbol - Departamental Ucayali",
    "hide_apps": ["auth"],
    "icons": {
        "gestion.Documento": "fas fa-folder-open",
    },
    "show_ui_builder": False,
    "changeform_format": "single",
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "theme": "pulse",
    "sidebar": "sidebar-dark-danger",
    "navbar_bg": "bg-danger",
}


# ===================================================
# SEGURIDAD PRODUCCIÓN (CRÍTICO PARA RENDER)
# ===================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    
    # IMPORTANTE: Esto permite loguearse desde el dominio de Render
    # Si no pones esto, te saldrá error "CSRF verification failed"
    CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']