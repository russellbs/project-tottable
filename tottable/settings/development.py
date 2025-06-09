from .base import *
import logging

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # You can change this to DEBUG for more output
    },
}

# Stripe TEST keys
STRIPE_SECRET_KEY = 'sk_test_51RVFsUAX7DzHjpeaGbeICN9QQppwQz17LR9lUs7ksb2bxKPFhHPjrYhLheOFXtsvpvzlEunbuZWJPwZ5RNqkrGeh00MtDhOIOw'
STRIPE_PUBLIC_KEY = 'pk_test_51RVFsUAX7DzHjpeafA07ugzkXQX019Wd3A01s5UdCR3EKbc1cL37r67bgj0Yb2uI3BuPwK1DgjKeXLpjfmjdckQM00H1uVzeIa'
STRIPE_PRICE_ID = 'price_1RVzkzAX7DzHjpea3iFuWlGU'
# If you're skipping webhooks for now, just leave this as-is or empty
STRIPE_WEBHOOK_SECRET = 'whsec_2ccf64eae3bbe7f4c740b41f71cf28f054538fb067eade5c041d78ac4c92d4c5'