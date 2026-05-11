from decouple import Csv, config

from .base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", cast=Csv())

# Security headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Sentry
import sentry_sdk  # noqa: E402
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=config("SENTRY_DSN", default=""),
    integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)
