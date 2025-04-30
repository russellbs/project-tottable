from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Stripe TEST keys
STRIPE_SECRET_KEY = 'sk_test_51PwlzZ02MR7uRsJ8qabyUFj8WnwigCT8CjLjdOwQpDMD3l0y2s1x2tyPu8xdVrc7IvB3jk5Gfpf8UPsHf7t6ubi4002mhEI5Vh'
STRIPE_PUBLIC_KEY = 'pk_test_51PwlzZ02MR7uRsJ8iDOSBsmpqkbaLcguKrPPXk7bOe0JCPzhNEAFiFwz9diqOdpVO8zFEtgcj1ckj7mrZ37nfA27001AsuqU1K'
STRIPE_PRICE_ID = 'price_1Q1oM602MR7uRsJ8upuf0TDl'
# If you're skipping webhooks for now, just leave this as-is or empty
STRIPE_WEBHOOK_SECRET = ''