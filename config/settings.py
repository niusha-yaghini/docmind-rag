"""Django settings. Everything environment-specific comes from env vars (see .env.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in env(name, default).split(",") if v.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "documents",
    "qa",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "docmind"),
        "USER": env("POSTGRES_USER", "docmind"),
        "PASSWORD": env("POSTGRES_PASSWORD", "docmind"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# REST framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Level 1: the API is open. No authentication classes also means Swagger "Try it out"
    # works even while you are logged in to /admin (no CSRF round-trip).
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DocMind RAG API",
    "DESCRIPTION": "Document question answering: upload docx files, search them, ask questions.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ---------------------------------------------------------------------------
# RAG / LLM
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = env("LLM_MODEL")
LLM_FALLBACK_MODELS = env_list("LLM_FALLBACK_MODELS")
LLM_TIMEOUT_SECONDS = int(env("LLM_TIMEOUT_SECONDS", "60"))

EMBEDDING_MODEL = env("EMBEDDING_MODEL", "liquid/lfm-2.5-embedding-350m:free")
# Fixed by the VectorField in documents/models.py. Changing it needs a new migration + reindex.
EMBEDDING_DIM = int(env("EMBEDDING_DIM", "1024"))
EMBEDDING_BATCH_SIZE = int(env("EMBEDDING_BATCH_SIZE", "32"))

CHUNK_SIZE = int(env("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(env("CHUNK_OVERLAP", "150"))
RETRIEVAL_CANDIDATES = int(env("RETRIEVAL_CANDIDATES", "20"))
RETRIEVAL_TOP_K = int(env("RETRIEVAL_TOP_K", "5"))
RRF_K = 60

MAX_UPLOAD_BYTES = int(env("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
