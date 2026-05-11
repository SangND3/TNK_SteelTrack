from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar (optional — add to dev deps if needed)
INTERNAL_IPS = ["127.0.0.1"]

# Faster password hashing in dev
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Show emails in console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable WhiteNoise compression in dev
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
