from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from allauth.exceptions import ImmediateHttpResponse
from django.conf import settings
from django.contrib.auth import get_user_model
import stripe
import logging

from base.models import PreSignupSocial, UserProfile

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY
User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # If the social account is already linked, let Allauth proceed
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get("email")
        name = sociallogin.account.extra_data.get("name")
        uid = sociallogin.account.uid
        provider = sociallogin.account.provider

        logger.info(f"OAuth signup triggered for email: {email}, uid: {uid}, provider: {provider}")

        # If user already exists (active or not), let Allauth proceed
        if User.objects.filter(email=email).exists():
            logger.info(f"User already exists for email {email}, skipping new Stripe session.")
            return

        # Create a PreSignupSocial record
        presignup, _ = PreSignupSocial.objects.get_or_create(
            uid=uid,
            defaults={
                'email': email,
                'first_name': name,
                'provider': provider,
                'stripe_checkout_session_id': '',
            }
        )

        # Create inactive user and profile for later activation via webhook
        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': name,
                'is_active': False,
            }
        )
        UserProfile.objects.get_or_create(user=user)

        # ✅ Get selected plan from session or fallback to monthly
        selected_plan = (
            request.GET.get("selected_plan") or
            request.session.get("selected_plan") or
            "monthly"
        )
        price_id = (
            settings.STRIPE_YEARLY_PRICE_ID
            if selected_plan == "yearly"
            else settings.STRIPE_MONTHLY_PRICE_ID
        )
        logger.info(f"Selected plan: {selected_plan}, using price ID: {price_id}")

        # Stripe checkout session setup
        base_url = request.build_absolute_uri("/")[:-1] if not settings.DEBUG else "https://cb47-62-167-164-221.ngrok-free.app"
        success_url = f"{base_url}{reverse('stripe_oauth_success')}?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}{reverse('signup-cancelled')}"

        checkout_session = stripe.checkout.Session.create(
            mode='subscription',
            payment_method_types=['card'],
            customer_email=email,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            subscription_data={
                'trial_period_days': 14
            },
            allow_promotion_codes=True,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'presignup_id': presignup.id
            },
        )

        # Update presignup record with Stripe session ID
        presignup.stripe_checkout_session_id = checkout_session.id
        presignup.save(update_fields=["stripe_checkout_session_id"])

        # Save session values
        request.session['oauth_checkout_session_id'] = checkout_session.id
        request.session['selected_plan'] = selected_plan

        logger.info(f"Redirecting to Stripe Checkout session: {checkout_session.url}")
        raise ImmediateHttpResponse(redirect(checkout_session.url))
