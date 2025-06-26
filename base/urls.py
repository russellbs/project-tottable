from django.urls import path, include
from . import views
from .views import test_meal_plan_email, PreSignupView, PostPaymentView, stripe_webhook, signup_cancelled, redirect_after_oauth_login, stripe_oauth_success, set_plan
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('profile/', views.profile, name='profile'),
    path('add-child/', views.add_child, name='add_child'),
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard page
    path('meal-plan/', views.meal_plan, name='meal_plan'),
    path('recipe-library/', views.recipe_library, name='recipe_library'),
    path('recipes/<str:id>/', views.recipe_detail, name='recipe_detail'),  # Updated to use string IDs
    path('add-child/', views.add_child, name='add_child'),
    path('edit-child/', views.edit_child, name='edit_child'),  # New edit child view
    path('get-child/<int:child_id>/', views.get_child, name='get_child'),  # Fetch child data
    path('delete-child/<int:child_id>/', views.delete_child, name='delete_child'),  # Delete child
    path('dashboard/swap/<str:recipe_id>/', views.dashboard_swap, name='dashboard_swap'),
    path('update_within_week_preferences/', views.update_within_week_preferences, name='update_within_week_preferences'),
    path('regenerate-meal-plan/<int:child_id>/', views.regenerate_meal_plan, name='regenerate_meal_plan'),
    path("test-email/", test_meal_plan_email, name="test_meal_plan_email"),
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    path('remove-meal/', views.remove_meal, name='remove_meal'),
    path("logout/", LogoutView.as_view(next_page="landing_page"), name="logout"),
    path("login/", LoginView.as_view(template_name="login.html"), name="login"),
    path('signup/', PreSignupView.as_view(), name='pre-signup'),
    path('post-payment/', PostPaymentView.as_view(), name='post-payment'),
    path('signup-cancelled/', signup_cancelled, name='signup-cancelled'),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('cancel-subscription/', views.cancel_subscription, name='cancel_subscription'),
    path('remove-meal/', views.remove_meal, name='remove_meal'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('update-exclude-purees/', views.update_exclude_purees, name='update_exclude_purees'),
    path('contact/', views.contact, name='contact'),
    path('accounts/', include('allauth.urls')),
    path("redirect-after-oauth/", redirect_after_oauth_login, name="redirect_after_oauth_login"),
    path("stripe-oauth-success/", stripe_oauth_success, name="stripe_oauth_success"),
    path("set-plan/", set_plan, name="set-plan"),
]

# Serve media files only during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)