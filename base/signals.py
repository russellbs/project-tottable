from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from django.shortcuts import reverse
from django.conf import settings
import stripe

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a UserProfile whenever a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the UserProfile whenever the User is saved.
    """
    instance.profile.save()

stripe.api_key = settings.STRIPE_SECRET_KEY

@receiver(user_signed_up)
def handle_google_presignup(sender, request, user, **kwargs):
    """
    Intercept Google OAuth signups to redirect to Stripe before activating user.
    """
    # Temporarily deactivate user until payment is confirmed
    user.is_active = False
    user.save()

    # Store first name from Google if available
    social_account = user.socialaccount_set.first()
    if social_account:
        first_name = social_account.extra_data.get('given_name')
        if first_name:
            user.first_name = first_name
            user.save()

    # Create Stripe Checkout Session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': settings.STRIPE_PRICE_ID,
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(reverse('stripe_oauth_success')) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=request.build_absolute_uri(reverse('signup_cancelled')),
        metadata={
            'user_id': user.id
        }
    )

    # Store checkout session ID in session to check it later
    request.session['oauth_checkout_session_id'] = checkout_session.id

    # Redirect response doesn't work here — we'll instead catch it in the view