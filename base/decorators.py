# decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.utils.timezone import now
import logging

logger = logging.getLogger(__name__)

def trial_or_subscribed_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        profile = getattr(user, "profile", None)

        if not profile:
            return redirect("upgrade_required")

        trial_end = getattr(profile, "trial_end_date", None)
        sub_id    = getattr(profile, "stripe_subscription_id", None)

        in_trial  = bool(trial_end and now() < trial_end)
        has_paid  = bool(sub_id)  # single source of truth for “subscribed”

        logger.info(
            "[GUARD] path=%s user=%s trial_end=%s now=%s in_trial=%s has_paid=%s",
            request.path, getattr(user, "email", None), trial_end, now(), in_trial, has_paid
        )

        # Allow if still in trial
        if in_trial:
            return view_func(request, *args, **kwargs)

        # After trial: allow only if we have a real Stripe subscription id
        if has_paid:
            return view_func(request, *args, **kwargs)

        # Otherwise, block
        return redirect("upgrade_required")

    return _wrapped_view
