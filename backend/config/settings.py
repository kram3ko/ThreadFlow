import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")

APP_ENV = os.getenv("APP_ENV", "development")
if APP_ENV not in {"development", "production"}:
    raise ImproperlyConfigured("APP_ENV must be development or production")

INSECURE_SECRET_DEFAULT = "local-only-insecure-secret"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", INSECURE_SECRET_DEFAULT)
if APP_ENV == "production" and SECRET_KEY == INSECURE_SECRET_DEFAULT:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured in production")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split(",") if host]
CSRF_TRUSTED_ORIGINS = [
    origin
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8080").split(",")
    if origin
]
CORS_ALLOWED_ORIGINS = [
    origin
    for origin in os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:8080").split(",")
    if origin
]
COOKIE_SECURE = os.getenv("COOKIE_SECURE", str(APP_ENV == "production")).lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "Lax")
ACCESS_COOKIE_NAME = os.getenv("ACCESS_COOKIE_NAME", "threadflow_access")
REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "threadflow_refresh")
CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "threadflow_csrftoken")


def jwt_secret(name: str, development_suffix: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    if APP_ENV == "production":
        raise ImproperlyConfigured(f"{name} must be configured in production")
    return f"{SECRET_KEY}:{development_suffix}"


JWT_ACCESS_SECRET = jwt_secret("JWT_ACCESS_SECRET", "access")
JWT_REFRESH_SECRET = jwt_secret("JWT_REFRESH_SECRET", "refresh")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER", "threadflow")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "threadflow-spa")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "15"))
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "14"))
JWT_REFRESH_ROTATION = os.getenv("JWT_REFRESH_ROTATION", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL")
CAPTCHA_TTL_SECONDS = int(os.getenv("CAPTCHA_TTL_SECONDS", "300"))
CAPTCHA_MAX_ATTEMPTS = int(os.getenv("CAPTCHA_MAX_ATTEMPTS", "3"))
COMMENT_RATE_LIMIT = os.getenv("RATE_LIMIT_COMMENT_PER_MINUTE", "10")
COMMENT_RATE_LIMIT_PER_MINUTE = int(COMMENT_RATE_LIMIT.split("/", maxsplit=1)[0])
VOTE_RATE_LIMIT = os.getenv("RATE_LIMIT_VOTE_PER_MINUTE", "60")
VOTE_RATE_LIMIT_PER_MINUTE = int(VOTE_RATE_LIMIT.split("/", maxsplit=1)[0])
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", "threadflow")
KAFKA_CONSUMER_GROUP_PREFIX = os.getenv("KAFKA_CONSUMER_GROUP_PREFIX", "threadflow")
KAFKA_RETRY_MAX_ATTEMPTS = int(os.getenv("KAFKA_RETRY_MAX_ATTEMPTS", "5"))
KAFKA_RETRY_BACKOFF_SECONDS = float(os.getenv("KAFKA_RETRY_BACKOFF_SECONDS", "5"))
# comments_updated and attachments_uploaded are reserved by the task's topic
# set; they have no active producer or consumer yet.
KAFKA_TOPICS = {
    "comments_created": os.getenv("KAFKA_TOPIC_COMMENTS_CREATED", "comments.created"),
    "comments_updated": os.getenv("KAFKA_TOPIC_COMMENTS_UPDATED", "comments.updated"),
    "attachments_uploaded": os.getenv("KAFKA_TOPIC_ATTACHMENTS_UPLOADED", "attachments.uploaded"),
    "search_index": os.getenv("KAFKA_TOPIC_SEARCH_INDEX", "search.index"),
    "retry": os.getenv("KAFKA_TOPIC_RETRY", "events.retry"),
    "dlq": os.getenv("KAFKA_TOPIC_DLQ", "events.dlq"),
}
OUTBOX_BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "100"))
OUTBOX_POLL_INTERVAL_SECONDS = float(os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "1"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "8001"))
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "threadflow-comments-v1")
ELASTICSEARCH_REQUEST_TIMEOUT_SECONDS = int(
    os.getenv("ELASTICSEARCH_REQUEST_TIMEOUT_SECONDS", "10")
)
ATTACHMENT_MAX_BYTES = int(os.getenv("ATTACHMENT_MAX_BYTES", "10485760"))
TXT_MAX_BYTES = int(os.getenv("TXT_MAX_BYTES", "102400"))
IMAGE_MAX_WIDTH = int(os.getenv("IMAGE_MAX_WIDTH", "320"))
IMAGE_MAX_HEIGHT = int(os.getenv("IMAGE_MAX_HEIGHT", "240"))

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "apps.accounts",
    "apps.captcha",
    "apps.comments",
    "apps.attachments",
    "apps.events",
    "apps.search",
    "apps.observability",
]

MIDDLEWARE = [
    "apps.observability.middleware.MetricsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csp",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "threadflow"),
            "USER": os.getenv("POSTGRES_USER", "threadflow"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "threadflow"),
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "threadflow.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_SAMESITE = COOKIE_SAMESITE
CORS_ALLOW_CREDENTIALS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "base-uri": [CSP.SELF],
    "object-src": [CSP.NONE],
    "frame-ancestors": [CSP.NONE],
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "NUM_PROXIES": int(os.getenv("RATE_LIMIT_NUM_PROXIES", "1")),
}

CACHES = {
    "default": {
        "BACKEND": (
            "django.core.cache.backends.redis.RedisCache"
            if REDIS_URL
            else "django.core.cache.backends.locmem.LocMemCache"
        ),
        "LOCATION": REDIS_URL or "threadflow-local",
        "KEY_PREFIX": os.getenv("REDIS_CACHE_PREFIX", "threadflow"),
    }
}

# RedisPubSubChannelLayer keeps a stable subscription; the classic
# RedisChannelLayer's blocking receive periodically raises redis TimeoutError
# on idle sockets and drops the WebSocket.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": (
            "channels_redis.pubsub.RedisPubSubChannelLayer"
            if REDIS_URL
            else "channels.layers.InMemoryChannelLayer"
        ),
        **(
            {
                "CONFIG": {
                    "hosts": [REDIS_URL],
                    "prefix": os.getenv("WS_CHANNEL_PREFIX", "threadflow:ws"),
                }
            }
            if REDIS_URL
            else {}
        ),
    }
}

if os.getenv("S3_ENDPOINT_URL"):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": os.getenv("S3_BUCKET", "threadflow"),
                "access_key": os.getenv("S3_ACCESS_KEY_ID"),
                "secret_key": os.getenv("S3_SECRET_ACCESS_KEY"),
                "endpoint_url": os.getenv("S3_ENDPOINT_URL"),
                "region_name": os.getenv("S3_REGION", "us-east-1"),
                "use_ssl": os.getenv("S3_USE_SSL", "false").lower() == "true",
                "default_acl": None,
                "querystring_auth": True,
                "file_overwrite": False,
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

SPECTACULAR_SETTINGS = {
    "TITLE": "ThreadFlow API",
    "DESCRIPTION": "REST API for threaded comments, authentication, attachments and search.",
    "VERSION": os.getenv("APP_VERSION", "0.1.0"),
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api",
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
