from django.urls import path
from . import views

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
    path('update_across_week_preferences/', views.update_across_week_preferences, name='update_across_week_preferences'),
]
