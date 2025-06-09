from .base import *

DEBUG = False
ALLOWED_HOSTS = ['tottable.com', 'www.tottable.com', '172.232.61.64']

CSRF_TRUSTED_ORIGINS = ['https://tottable.com', 'https://www.tottable.com']


# Stripe TEST keys
STRIPE_SECRET_KEY = 'sk_test_51RVFsUAX7DzHjpeaGbeICN9QQppwQz17LR9lUs7ksb2bxKPFhHPjrYhLheOFXtsvpvzlEunbuZWJPwZ5RNqkrGeh00MtDhOIOw'
STRIPE_PUBLIC_KEY = 'pk_test_51RVFsUAX7DzHjpeafA07ugzkXQX019Wd3A01s5UdCR3EKbc1cL37r67bgj0Yb2uI3BuPwK1DgjKeXLpjfmjdckQM00H1uVzeIa'
STRIPE_PRICE_ID = 'price_1RVzkzAX7DzHjpea3iFuWlGU'
# If you're skipping webhooks for now, just leave this as-is or empty
STRIPE_WEBHOOK_SECRET = 'whsec_2ccf64eae3bbe7f4c740b41f71cf28f054538fb067eade5c041d78ac4c92d4c5'

# Example extra security settings you might want:
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'
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
