import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-kaho-dev-key-change-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'storages',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# Railway injecte DATABASE_URL ; en local on retombe sur les variables DB_*
DATABASES = {
    'default': dj_database_url.config(
        default=(
            f"postgresql://{config('DB_USER', default='postgres')}:"
            f"{config('DB_PASSWORD', default='postgres')}@"
            f"{config('DB_HOST', default='localhost')}:"
            f"{config('DB_PORT', default='5432')}/"
            f"{config('DB_NAME', default='kaho_db')}"
        ),
        conn_max_age=600,
    )
}

# Auth User Model
AUTH_USER_MODEL = 'core.User'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
PASSWORD_RESET_TIMEOUT = 60 * 60  # 1 h

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-FR'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Derrière le proxy Railway (HTTPS terminé en amont)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000', cast=Csv())

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Google Cloud Storage — documents privés (pièces d'identité, NEPH, contrats)
# GCS_CREDENTIALS = contenu du JSON du compte de service, brut ou encodé en base64
USE_GCS = config('USE_GCS', default=False, cast=bool)
if USE_GCS:
    import base64
    import json
    from google.oauth2 import service_account

    _raw = config('GCS_CREDENTIALS')
    try:
        _info = json.loads(_raw)
    except ValueError:
        _info = json.loads(base64.b64decode(_raw))
    GS_CREDENTIALS = service_account.Credentials.from_service_account_info(_info)
    GS_BUCKET_NAME = config('GCS_BUCKET_NAME')
    GS_PROJECT_ID = _info.get('project_id')
    GS_DEFAULT_ACL = None          # bucket en accès uniforme : pas d'ACL par objet
    GS_QUERYSTRING_AUTH = True     # URLs signées temporaires pour les fichiers privés
    GS_EXPIRATION = timedelta(minutes=30)
    GS_FILE_OVERWRITE = False
    STORAGES = {
        'default': {'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# Frontend (liens dans les emails)
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# Réservation
BOOKING_MIN_NOTICE_HOURS = config('BOOKING_MIN_NOTICE_HOURS', default=24, cast=int)
BOOKING_CANCEL_DEADLINE_HOURS = config('BOOKING_CANCEL_DEADLINE_HOURS', default=48, cast=int)

# CORS
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())

# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Paris'
# Sans Redis configuré, les tâches s'exécutent inline (dev local, ou prod sans worker)
CELERY_TASK_ALWAYS_EAGER = not config('REDIS_URL', default='')

# Email — SMTP (Brevo : smtp-relay.brevo.com, login = email du compte, mot de passe = clé SMTP)
EMAIL_HOST = config('EMAIL_HOST', default='smtp-relay.brevo.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Kaho <noreply@kaho-auto-ecole.fr>')
# Sans identifiants SMTP, les emails sont affichés dans les logs (dev / avant configuration)
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST_PASSWORD
    else 'django.core.mail.backends.console.EmailBackend'
)

# SMS via Brevo (clé API v3, différente de la clé SMTP). Sans clé, aucun SMS n'est envoyé.
BREVO_API_KEY = config('BREVO_API_KEY', default='')
BREVO_SMS_SENDER = config('BREVO_SMS_SENDER', default='Kaho')  # 11 caractères alphanumériques max

# Stripe Configuration
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')

# OTP Configuration
OTP_TOTP_ISSUER = 'Kaho'
OTP_LOGIN_URL = '/auth/login/'

# Magic Link Token Expiry (in hours)
MAGIC_LINK_TOKEN_EXPIRY = 24
