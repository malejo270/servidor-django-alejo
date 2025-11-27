"""
Django settings for emcali_app project.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------
# 🔐 SEGURIDAD
# ----------------------------------------------------
SECRET_KEY = 'django-insecure-#ie#8jer^tp!1dp+dpxz6upgp!rze2(6$#q@!c5#5=g7#$u$0_'

DEBUG = False  # En PythonAnywhere debe estar en False

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'malejo.pythonanywhere.com',
]

# ----------------------------------------------------
# 📦 APPS
# ----------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mantenimiento',
]

# ----------------------------------------------------
# 🔧 MIDDLEWARE
# ----------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'emcali_app.urls'

# ----------------------------------------------------
# 🎨 TEMPLATE CONFIG
# ----------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'mantenimiento.context_processors.user_role_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'emcali_app.wsgi.application'

# ----------------------------------------------------
# 🗄 BASE DE DATOS (MySQL en PythonAnywhere)
# ----------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'malejo$default',
        'USER': 'malejo',
        'PASSWORD': 'holahola123',
        'HOST': 'malejo.mysql.pythonanywhere-services.com',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ----------------------------------------------------
# 🔐 PASSWORD VALIDATION
# ----------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------------------------------
# 🌍 INTERNACIONALIZACIÓN
# ----------------------------------------------------
LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# ----------------------------------------------------
# 📂 STATIC FILES (CORREGIDO PARA PYTHONANYWHERE)
# ----------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = '/home/malejo/emcali_app/staticfiles/'

# 🔥 ELIMINA STATICFILES_DIRS en producción - CAUSA CONFLICTOS
# STATICFILES_DIRS = []

# ----------------------------------------------------
# 📸 MEDIA FILES (CORREGIDO)
# ----------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = '/home/malejo/emcali_app/media/'  # ← RUTA ABSOLUTA CORREGIDA

# ----------------------------------------------------
# 📧 EMAIL CONFIGURATION
# ----------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "alejandropl2706@gmail.com"
EMAIL_HOST_PASSWORD = "ymld ozsd ryfn dhdb"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ----------------------------------------------------
# 🔑 PRIMARY KEY
# ----------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------------------------------
# ⚙️ CONFIGURACIÓN ADICIONAL PARA PYTHONANYWHERE
# ----------------------------------------------------

# Configuración para archivos subidos
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Seguridad adicional en producción
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True