"""
Django settings for KVER project.
Локально: скопируйте .env.example в .env и при необходимости измените значения.
На хостинге: задайте переменные в панели (PythonAnywhere → Web → Environment variables).
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Безопасность ---
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-dev-only-do-not-use-in-production',
)

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv(),
)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

# --- Приложения ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'accounts',
    'core',
    'events',
    'media_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
                'accounts.context_processors.messenger_unread',
                'accounts.context_processors.linked_accounts',
                'accounts.context_processors.notifications_context',
                'accounts.context_processors.liked_photo_cards_context',
                'media_app.context_processors.moderation_context',
                'media_app.context_processors.liked_covers_context',
                'core.context_processors.kver_admin_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- База данных (SQLite; для продакшена на бесплатном хостинге достаточно) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / config('DB_NAME', default='db.sqlite3'),
    }
}

# --- Пароли ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Локализация ---
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# --- Статика и медиа ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Crispy Forms ---
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

AUTH_USER_MODEL = 'accounts.CustomUser'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# --- YouTube API (опционально) ---
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY', default='')

# --- Модерация комментариев ---
COMMENT_STOP_WORDS = [
    'spam', 'scam', 'xxx', 'porn', 'порно', 'спам',
    'мошенник', 'мошенничество', 'реклама', 'casino', 'казино',
    'наркотик', 'наркота', 'сука', 'блять', 'блядь', 'хуй',
    'пизда', 'ебать', 'fuck', 'shit',     'bitch',
]

# --- Администрация KVER (pk суперпользователя; если None — первый superuser) ---
KVER_ADMIN_USER_ID = config('KVER_ADMIN_USER_ID', default=None, cast=lambda v: int(v) if v else None)

# --- Настройки для продакшена (DEBUG=False) ---
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # На PythonAnywhere включён HTTPS; локально при DEBUG=False задайте USE_HTTPS=False в .env
    if config('USE_HTTPS', default=True, cast=bool):
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
