from .base import *

DEBUG = False
ALLOWED_HOSTS = ['tottable.com', 'www.tottable.com']

# Stripe LIVE keys
STRIPE_PUBLIC_KEY = 'pk_live_...'
STRIPE_SECRET_KEY = 'sk_live_...'
STRIPE_PRICE_ID = 'price_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'

# Example extra security settings you might want:
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/home/webapp/tottable/django-error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
