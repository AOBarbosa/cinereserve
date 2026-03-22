from .base import *  # noqa: F401, F403

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use dummy cache in tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # type: ignore[index]  # noqa: F405
    "anon": "10000/min",
    "user": "10000/min",
}
