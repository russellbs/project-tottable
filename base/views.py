from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Ingredient, Child, Recipe, MealPlan, Meal, RecipeIngredient, UserProfile, PreSignupSocial
from .forms import AddChildForm, WithinWeekPreferencesForm, AcrossWeekPreferencesForm, PreSignupForm  # Import the AddChildForm
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now, make_aware
from django.conf import settings
from django.views import View
from django.urls import reverse
import logging
import json
from django.http import JsonResponse
import random
import stripe
from datetime import timedelta
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.provider import GoogleProvider
from django.contrib.auth import authenticate
from .decorators import trial_or_subscribed_required


stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


def landing_page(request):
    return render(request, 'landing.html')

# View for displaying the user's profile and handling the Add Child and UserPreferences Forms
@login_required
@trial_or_subscribed_required
def profile(request):
    user = request.user
    ingredients = Ingredient.objects.all()
    allergens = Ingredient.objects.exclude(allergen_type__isnull=True).exclude(allergen_type__exact='').values_list('allergen_type', flat=True).distinct()
    children = Child.objects.filter(parent=user)

    profile = user.profile
    trial_active = profile.trial_end_date and now() < profile.trial_end_date

    trial_days_remaining = None
    if profile.trial_end_date and now() < profile.trial_end_date:
        trial_days_remaining = (profile.trial_end_date - now()).days

    # Prepare Within-Week Preferences
    within_week_preferences_flat = [
    {"meal": meal, "value": profile.get_within_week_display(meal)}
    for meal in ["breakfast", "lunch", "dinner", "snack"]
    ]

    # Prepare Across-Week Preferences
    across_week_preferences_flat = [
        {"meal": meal, "value": profile.across_week_preferences.get(meal, "No preference selected").title()}
        for meal in ["breakfast", "lunch", "dinner", "snack"]
    ]

    # 👉 Show welcome modal if no children yet
    show_welcome = not children.exists()

    # ✅ Check for TikTok conversion event and remove it from session
    pixel_conversion_event = request.session.get('pixel_conversion_event')
    if pixel_conversion_event:
        del request.session['pixel_conversion_event']
    else:
        pixel_conversion_event = None  # Explicitly set to None if not found
    
    context = {
        "user": user,
        "ingredients": ingredients,
        "children": children,
        "within_week_preferences_flat": within_week_preferences_flat,
        "across_week_preferences_flat": across_week_preferences_flat,
        "allergens": allergens,
        "show_welcome": show_welcome,
        "trial_active": trial_active,
        "trial_days_remaining": trial_days_remaining,
        "show_preferences_form": True,
    }

    return render(request, "profile.html", context)

def generate_meal_plan(child_id, week_offset=0):
    logger.info(f"⚙️ generate_meal_plan called for child_id={child_id}, week_offset={week_offset}")
    from datetime import timedelta
    from django.utils.timezone import now

    child = get_object_or_404(Child, id=child_id)
    dislikes = child.dislikes_ingredients.all()
    allergies = child.allergies.split(',') if child.allergies else []

    # Determine the start and end of the requested week
    today = now().date()
    start_date = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    end_date = start_date + timedelta(days=6)

    # Check if a meal plan for this specific week already exists
    meal_plan, created = MealPlan.objects.get_or_create(
        child=child, start_date=start_date, end_date=end_date
    )

    logger.info(f"MealPlan {'created' if created else 'already exists'} for child {child_id} from {start_date} to {end_date}")

    if not created:
        # If a meal plan already exists, return it
        return meal_plan

    # Meal assignment logic
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meal_types = ["Breakfast", "Lunch", "Dinner", "Snack"]
    profile = child.parent.profile

    for meal_type in meal_types:
        preferred_level = profile.within_week_preferences.get(meal_type.lower(), "medium").lower()
        variety_mapping = {"high": (6, 7), "medium": (4, 5), "low": (2, 3), "no": (1, 1)}
        min_variety, max_variety = variety_mapping.get(preferred_level, (4, 5))

        child_age = child.age_in_months()

        recipe_qs = Recipe.objects.filter(
            meal_types__name=meal_type,
            min_age_months__lte=child_age,
            max_age_months__gte=child_age
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__allergen_type__in=allergies
        )

        if profile.exclude_purees:
            recipe_qs = recipe_qs.exclude(is_puree=True)

        possible_recipes = list(recipe_qs)

        num_unique_recipes = min(len(possible_recipes), random.randint(min_variety, max_variety))

        if num_unique_recipes == 0:
            print(f"⚠️ No valid recipes found for {meal_type}. Skipping meal plan generation.")
            continue

        selected_recipes = random.sample(possible_recipes, num_unique_recipes)

        for day_index, day in enumerate(days):
            if preferred_level == "no":
                selected_recipe = selected_recipes[0]
            elif preferred_level == "high":
                selected_recipe = selected_recipes[day_index % len(selected_recipes)]
            else:
                selected_recipe = selected_recipes[(day_index // 2) % len(selected_recipes)]

            meal, _ = Meal.objects.get_or_create(meal_plan=meal_plan, day=day)
            setattr(meal, meal_type.lower(), selected_recipe)
            meal.save()

    return meal_plan




# Updated Add Child View (if separate endpoint is still required)
@login_required
def add_child(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Extract data from POST request
            name = request.POST.get('name')
            dob = request.POST.get('dob')
            likes = request.POST.getlist('likes_ingredients')  # Multiple values
            dislikes = request.POST.getlist('dislikes_ingredients')  # Multiple values
            allergies = request.POST.get('allergies', '')

            # Validate required fields
            if not name or not dob:
                return JsonResponse({'success': False, 'error': 'Name and Date of Birth are required.'}, status=400)

            # Convert dob to a date object
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

            # Create and save the child
            child = Child.objects.create(
                name=name,
                dob=dob,
                parent=request.user,
                allergies=allergies
            )
            child.likes_ingredients.set(likes)
            child.dislikes_ingredients.set(dislikes)
            child.save()

            logger.error(f"✅ Child saved: {child.name}, generating meal plan...")

            try:
                meal_plan = generate_meal_plan(child.id)
                logger.error("✅ Meal plan generation completed successfully.")
                meal_plan_created = True
            except Exception as e:
                logger.error(f"❌ Meal plan generation failed: {e}")
                meal_plan_created = False

            # Return JSON response
            return JsonResponse({
                'success': True,  # Added this key
                'meal_plan_created': meal_plan_created,
                'name': child.name,
                'dob': child.dob.strftime('%Y-%m-%d'),
                'likes_ingredients': list(child.likes_ingredients.values_list('name', flat=True)),
                'dislikes_ingredients': list(child.dislikes_ingredients.values_list('name', flat=True)),
                'allergies': child.allergies or '',
            })
        except Exception as e:
            logger.error(f"Error in add_child view: {e}")  # Log the error
            return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def get_child(request, child_id):
    try:
        child = Child.objects.get(id=child_id, parent=request.user)
        return JsonResponse({
            'id': child.id,
            'name': child.name,
            'dob': child.dob.strftime('%Y-%m-%d'),
            'likes_ingredients': list(child.likes_ingredients.values_list('id', flat=True)),
            'dislikes_ingredients': list(child.dislikes_ingredients.values_list('id', flat=True)),
            'allergies': child.allergies,
        })
    except Child.DoesNotExist:
        return JsonResponse({'error': 'Child not found.'}, status=404)

@login_required
def edit_child(request):
    if request.method == 'POST':
        child_id = request.POST.get('child_id')
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        likes = request.POST.getlist('likes_ingredients')
        dislikes = request.POST.getlist('dislikes_ingredients')
        allergies = request.POST.get('allergies', '')

        try:
            # Fetch and update the child record
            child = Child.objects.get(id=child_id, parent=request.user)
            child.name = name
            child.dob = datetime.strptime(dob, '%Y-%m-%d').date()
            child.allergies = allergies
            child.likes_ingredients.set(likes)
            child.dislikes_ingredients.set(dislikes)
            child.save()

            return JsonResponse({'success': True})
        except Child.DoesNotExist:
            return JsonResponse({'error': 'Child not found.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def delete_child(request, child_id):
    if request.method == 'DELETE':
        try:
            child = Child.objects.get(id=child_id, parent=request.user)
            child.delete()
            return JsonResponse({'success': True})
        except Child.DoesNotExist:
            return JsonResponse({'error': 'Child not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


# Example meal plan data (replace with dynamic data from the database later)
DUMMY_MEAL_PLAN = [
    {
        'name': 'Monday',
        'breakfast': 'Pancakes',
        'lunch': 'Grilled Cheese',
        'dinner': 'Spaghetti Bolognese',
    },
    {
        'name': 'Tuesday',
        'breakfast': 'Oatmeal',
        'lunch': 'Chicken Salad',
        'dinner': 'Stir-fry Vegetables',
    },
    # Add more days as needed
]

@login_required
@trial_or_subscribed_required
def dashboard(request):
    user = request.user
    children = Child.objects.filter(parent=user)

    # Determine the week to display (default: current week)
    week_offset = int(request.GET.get("week", 0))
    today = timezone.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    displayed_week_start = current_week_start + timedelta(weeks=week_offset)
    displayed_week_end = displayed_week_start + timedelta(days=6)

    # Next Week logic (allows two weeks ahead)
    next_week_start = displayed_week_start + timedelta(days=7)
    previous_week_start = displayed_week_start - timedelta(days=7)
    next_week_available_date = current_week_start + timedelta(days=4)

    # Ensure a meal plan is available for the selected week
    meal_plans = []
    for child in children:
        meal_plan = MealPlan.objects.filter(
            child=child, start_date=displayed_week_start, end_date=displayed_week_end
        ).order_by("-created_at").first()

        if not meal_plan:
            print(f"Generating meal plan for {child.name}, Week Offset: {week_offset}")
            meal_plan = generate_meal_plan(child.id, week_offset)

        meal_plans.append((child, meal_plan))

    context = {
        "children": children,
        "meal_plans": meal_plans,
        "displayed_week_start": displayed_week_start,
        "displayed_week_end": displayed_week_end,
        "previous_week_start": previous_week_start,
        "next_week_start": next_week_start,
        "next_week_available_date": next_week_available_date,
        "week_offset": week_offset,
    }

    return render(request, "dashboard.html", context)





@login_required
def meal_plan(request):
    # Placeholder context
    context = {}
    return render(request, 'meal_plan.html', context)

@login_required
@trial_or_subscribed_required
def recipe_library(request):
    # Fetch all recipes
    recipes = Recipe.objects.all()

    # Check if the swap functionality is enabled
    swap_mode = request.GET.get('swap', '') == '1'
    meal_type = request.GET.get('meal_type', '')
    day = request.GET.get('day', '')

    # Apply search filters
    query = request.GET.get('query', '')
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) | 
            Q(ingredients__name__icontains=query)
        )

    # Meal type filter
    if meal_type:
        recipes = recipes.filter(meal_types__name__icontains=meal_type)

    # Age range filter
    age_range = request.GET.get('age_range', '')
    if age_range:
        if age_range == '6-9':
            recipes = recipes.filter(min_age_months__gte=6, max_age_months__lte=9)
        elif age_range == '9-12':
            recipes = recipes.filter(min_age_months__gte=9, max_age_months__lte=12)
        elif age_range == '12+':
            recipes = recipes.filter(min_age_months__gte=12)

    # Vegetarian and vegan filters
    vegetarian = request.GET.get('vegetarian', '')
    if vegetarian:
        recipes = recipes.filter(is_vegetarian=True)

    vegan = request.GET.get('vegan', '')
    if vegan:
        recipes = recipes.filter(is_vegan=True)

    # Exclude allergens
    exclude_allergens = request.GET.getlist('exclude_allergens')
    if exclude_allergens:
        recipes = recipes.exclude(ingredients__allergen_type__in=exclude_allergens)

    allergens = Ingredient.objects.exclude(
        allergen_type__in=['', 'None', 'Gluten-Free']
    ).values_list('allergen_type', flat=True).distinct()
    
    # Pagination
    paginator = Paginator(recipes.distinct(), 12)  # Show 12 recipes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for recipe in page_obj:
        recipe.has_potential_allergens = recipe.ingredients.filter(
            allergen_type__isnull=False
        ).exclude(
            allergen_type__in=['', 'None', 'Gluten-Free']
        ).exists()

    # 👶 Get the first child and their age in months
    children = Child.objects.filter(parent=request.user)
    selected_child = children.first()
    child_age_months = selected_child.age_in_months() if selected_child else None

    return render(request, 'recipe_library.html', {
        'page_obj': page_obj,
        'query': query,
        'meal_type': meal_type,
        'age_range': age_range,
        'swap_mode': swap_mode,
        'day': day,
        'allergens': allergens,
        'selected_child': selected_child,
        'child_age_months': child_age_months,
        'exclude_allergens': exclude_allergens,
    })

@login_required
@trial_or_subscribed_required
def recipe_detail(request, id):
    # Fetch the recipe using the string-based ID
    recipe = get_object_or_404(Recipe, id=id)
    
    # Split instructions by semicolon if available
    instructions = recipe.instructions.split(';') if recipe.instructions else []
    
    # Get swap mode parameters
    swap_mode = request.GET.get('swap', '') == '1'
    meal_type = request.GET.get('meal_type', '')
    day = request.GET.get('day', '')

    # Back link handling
    back_link = request.GET.get('from', 'recipe_library')  # Default to recipe library if `from` is not provided
    back_link_url = f"{back_link}?swap=1&meal_type={meal_type}&day={day}" if swap_mode else back_link

    # ✅ Add logic to get the current user's first child (or whichever one makes sense)
    child = request.user.children.first()
    child_name = child.name if child else None
    child_age_months = child.age_in_months() if child else None

    show_age_modal = child_age_months is not None and recipe.min_age_months > child_age_months

    allergen_ingredients = recipe.ingredients.filter(
        allergen_type__isnull=False
    ).exclude(
        allergen_type__in=['', 'None', 'Gluten-Free']
    )

    allergen_types = allergen_ingredients.values_list('allergen_type', flat=True).distinct()

    return render(request, 'recipe_detail.html', {
        'recipe': recipe,
        'instructions': instructions,
        'swap_mode': swap_mode,
        'meal_type': meal_type,
        'day': day,
        'back_link_url': back_link_url,
        'child_name': child_name,
        'child_age_months': child_age_months,
        'allergen_types': allergen_types,
        'show_age_modal': show_age_modal,
    })



def dashboard_swap(request, recipe_id):
    print(f"Received swap request for recipe ID: {recipe_id}")
    recipe = get_object_or_404(Recipe, id=recipe_id)
    meal_type = request.GET.get('meal_type')
    day = request.GET.get('day')
    week_offset = int(request.GET.get('week', 0))  # Get week offset from the request

    print(f"Meal type: {meal_type}, Day: {day}, Week offset: {week_offset}")

    # Calculate the start and end dates for the targeted week
    today = timezone.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    target_week_start = current_week_start + timedelta(weeks=week_offset)
    target_week_end = target_week_start + timedelta(days=6)

    print(f"Target week: {target_week_start} to {target_week_end}")

    # Find the corresponding MealPlan for the user and the calculated week
    meal_plan = MealPlan.objects.filter(
        child__parent=request.user,
        start_date=target_week_start,
        end_date=target_week_end
    ).first()

    if not meal_plan:
        print("MealPlan not found.")
        messages.error(request, "Meal plan not found.")
        return redirect('dashboard')

    print(f"MealPlan found: {meal_plan}")
    meal = meal_plan.meals.filter(day=day).first()
    if not meal:
        print(f"No meal found for day: {day}")
        messages.error(request, f"Meal for {day.capitalize()} not found.")
        return redirect('dashboard')

    print(f"Meal found: {meal}")
    if meal_type and hasattr(meal, meal_type):
        old_recipe = getattr(meal, meal_type, None)
        setattr(meal, meal_type, recipe)
        meal.save()
        print(f"Updated meal: {meal_type} swapped to {recipe}")
        messages.success(
            request,
            f"{old_recipe.title if old_recipe else 'Meal'} swapped for {recipe.title} successfully!"
        )
    else:
        print(f"Invalid meal type: {meal_type}")
        messages.error(request, "Invalid meal type.")
        return redirect('dashboard')

    return redirect('dashboard')

@login_required
def update_within_week_preferences(request):
    if request.method == "POST":
        profile = request.user.profile
        preferences = profile.within_week_preferences or {}
        
        # Update preferences from POST data
        preferences['breakfast'] = request.POST.get('breakfast', '')
        preferences['lunch'] = request.POST.get('lunch', '')
        preferences['dinner'] = request.POST.get('dinner', '')
        preferences['snack'] = request.POST.get('snack', '')

        # Save back to the profile
        profile.within_week_preferences = preferences

        # Update exclude_purees toggle
        profile.exclude_purees = request.POST.get("exclude_purees") == "on"

        profile.save()

        # Return updated preferences in the response
        return JsonResponse({"success": True, "preferences": preferences, "exclude_purees": profile.exclude_purees,})
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

@login_required
def regenerate_meal_plan(request, child_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."}, status=405)

    # Fetch the child
    child = get_object_or_404(Child, id=child_id, parent=request.user)

    # Determine the current week's start and end dates
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)

    # Retrieve the existing meal plan (ensuring we don’t create a new one)
    meal_plan = get_object_or_404(MealPlan, child=child, start_date=start_date, end_date=end_date)

    # Regenerate the meals while keeping the same meal plan
    updated_meal_plan = regenerate_meals_for_plan(meal_plan)

    # Print out the updated meals for debugging
    print(f"\nRegenerated Meal Plan ID: {meal_plan.id}")
    for meal in updated_meal_plan.meals.all():
        print(f"Day: {meal.day}, Breakfast: {meal.breakfast}, Lunch: {meal.lunch}, Dinner: {meal.dinner}, Snack: {meal.snack}")

    return JsonResponse({"success": True, "message": "Meal plan regenerated successfully."})

def regenerate_meals_for_plan(meal_plan):
    """Updates meals inside an existing meal plan without creating a new plan."""
    child = meal_plan.child
    dislikes = child.dislikes_ingredients.all()
    allergies = child.allergies.split(',') if child.allergies else []
    profile = child.parent.profile

    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    # Variety mapping
    variety_levels = {
        "high": (6, 7),  # Almost no repetition
        "medium": (4, 5),  # Meals repeat in pairs
        "low": (2, 3),  # More repetition, every 2 days
        "no": (1, 1),  # Same meal every day
    }

    # ✅ Step 1: Remove old meals but keep the meal plan
    meal_plan.meals.all().delete()

    # ✅ Step 2: Prepare meals across all days
    meal_assignments = {day: {} for day in days}

    for meal_type in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        preferred_level = profile.within_week_preferences.get(meal_type.lower(), "medium").lower()
        min_variety, max_variety = variety_levels.get(preferred_level, (4, 5))
        num_unique_recipes = random.randint(min_variety, max_variety)

        # Fetch recipes
        child_age = child.age_in_months()

        # ✅ Build recipe queryset
        recipe_qs = Recipe.objects.filter(
            meal_types__name=meal_type,
            min_age_months__lte=child_age,
            max_age_months__gte=child_age
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__allergen_type__in=allergies
        )

        if profile.exclude_purees:
            recipe_qs = recipe_qs.exclude(is_puree=True)

        possible_recipes = list(recipe_qs)

        if not possible_recipes:
            continue  # Skip this meal type if no valid recipes

        if len(possible_recipes) < num_unique_recipes:
            selected_recipes = random.sample(possible_recipes, len(possible_recipes))
        else:
            selected_recipes = random.sample(possible_recipes, num_unique_recipes)

        # ✅ Step 3: Assign meals properly across the week
        i = 0
        for day_index, day in enumerate(days):
            # If "no variety," use the same recipe every day
            if preferred_level == "no":
                selected_recipe = selected_recipes[0]
            elif preferred_level == "high":
                selected_recipe = selected_recipes[day_index % len(selected_recipes)]
            else:
                if day_index % 2 == 0 and i < len(selected_recipes) - 1:
                    i += 1
                selected_recipe = selected_recipes[i % len(selected_recipes)]

            meal_assignments[day][meal_type.lower()] = selected_recipe

    # ✅ Step 4: Save the new meal assignments
    for day, meals in meal_assignments.items():
        Meal.objects.create(meal_plan=meal_plan, day=day, **meals)

    # ✅ Step 5: Print out the updated meal plan for debugging
    print(f"\n✅ Updated Meal Plan ID: {meal_plan.id}")
    for meal in meal_plan.meals.all():
        print(f"Day: {meal.day}, Breakfast: {meal.breakfast}, Lunch: {meal.lunch}, Dinner: {meal.dinner}, Snack: {meal.snack}")

    return meal_plan


def test_meal_plan_email(request):
    meal_plan = {
        "Monday": {"breakfast": "Baby Oatmeal", "lunch": "Sweet Potato Puree", "dinner": "Mashed Peas", "snack": "Banana Mash"},
        "Tuesday": {"breakfast": "Apple Cinnamon Porridge", "lunch": "Carrot-Chickpea Mash", "dinner": "Pumpkin Risotto", "snack": "Avocado Toast"},
        "Wednesday": {"breakfast": "Mini Broccoli Frittatas", "lunch": "Cheesy Soft Polenta", "dinner": "Turkey Bolognese", "snack": "Blueberry Bliss Smoothie"},
    }
    
    context = {
        "child_name": "Emma",
        "meal_plan": meal_plan,
        "meal_plan_url": "/meal-plan/",
        "shopping_list_url": "/shopping-list/",
        "swap_meal_url": "/swap-meal/",
        "preferences_url": "/preferences/",
    }
    
    return render(request, "meal_plan_email.html", context)


@login_required
@trial_or_subscribed_required
def shopping_list(request):
    user = request.user
    ingredients = {}

    # Handle week offset for navigation
    week_offset = int(request.GET.get('week', 0))
    current_week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
    displayed_week_start = current_week_start + timedelta(weeks=week_offset)
    displayed_week_end = displayed_week_start + timedelta(days=6)

    # Fetch MealPlans for the current user's children for the selected week
    meal_plans = MealPlan.objects.filter(
        child__parent=user,
        start_date=displayed_week_start,
        end_date=displayed_week_end
    )

    for meal_plan in meal_plans:
        for meal in meal_plan.meals.all():  # Iterate through each meal
            for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                recipe = getattr(meal, meal_type, None)
                if recipe:
                    recipe_ingredients = RecipeIngredient.objects.filter(recipe=recipe)
                    for item in recipe_ingredients:
                        name = item.ingredient.name
                        quantity = item.quantity
                        unit = item.unit

                        # Aggregate duplicate ingredients
                        if name in ingredients:
                            if ingredients[name]['unit'] == unit:
                                ingredients[name]['quantity'] += quantity
                            else:
                                # Handle unit mismatch gracefully
                                ingredients[name]['quantity'] += quantity
                                ingredients[name]['unit'] = f"{ingredients[name]['unit']} / {unit}"
                        else:
                            ingredients[name] = {'quantity': quantity, 'unit': unit}

    context = {
        'ingredients': ingredients,
        'displayed_week_start': displayed_week_start,
        'displayed_week_end': displayed_week_end,
        'week_offset': week_offset,
    }

    return render(request, 'shopping_list.html', context)


@login_required
@require_POST
def remove_meal(request):
    meal_id = request.POST.get('meal_id')
    meal_type = request.POST.get('meal_type')

    if not meal_id or not meal_type:
        return JsonResponse({'success': False, 'error': 'Missing parameters.'}, status=400)

    try:
        meal = Meal.objects.get(id=meal_id, meal_plan__child__parent=request.user)
        setattr(meal, meal_type, None)
        meal.save()
        return JsonResponse({'success': True})
    except Meal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Meal not found.'}, status=404)

class PreSignupView(View):
    def get(self, request):
        form = PreSignupForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request):
        form = PreSignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            password = form.cleaned_data['password']

            # Prevent duplicate signups
            if User.objects.filter(email=email).exists():
                form.add_error('email', 'Email already exists. Please log in.')
                return render(request, 'signup.html', {'form': form})

            # Create user immediately
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                password=password,
                is_active=True
            )

            # Set up 2-week trial in UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.trial_end_date = now() + timedelta(days=14)
            profile.subscription_status = 'trialing'
            profile.save()

            # Log the user in
            user = authenticate(request, username=email, password=password)
            login(request, user)

            # Pixel tracking
            request.session['pixel_conversion_event'] = 'subscribe'

            return redirect('profile')
        else:
            return render(request, 'signup.html', {'form': form})

class PostPaymentView(View):
    def get(self, request):
        signup_data = request.session.get('signup_data')
        if not signup_data:
            return redirect('signup-cancelled')

        email = signup_data['email']
        password = signup_data['password']

        user = User.objects.filter(email=email).first()
        if user:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            del request.session['signup_data']

            # ✅ Set the flag for TikTok pixel tracking
            request.session['pixel_conversion_event'] = 'subscribe'

            return redirect('profile')
        else:
            # Fallback: redirect them to a page suggesting to try again or contact support
            return redirect('signup-cancelled')

    
def signup_cancelled(request):
    session_id = (
        request.GET.get('session_id') or
        request.session.get('oauth_checkout_session_id') or
        request.session.get('form_checkout_session_id')
    )
    User = get_user_model()

    # Clean up OAuth signups
    if session_id:
        social_presignup = PreSignupSocial.objects.filter(stripe_checkout_session_id=session_id).first()
        if social_presignup:
            user = User.objects.filter(email=social_presignup.email, is_active=False).first()
            if user:
                user.delete()
            social_presignup.delete()
            request.session.pop('oauth_checkout_session_id', None)
            return redirect('landing_page')

    # Clean up form-based signups — just clear session, no model/user to delete
    request.session.pop('form_checkout_session_id', None)
    request.session.pop('signup_data', None)

    return redirect('landing_page')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.warning(f"❌ Webhook verification failed: {e}")
        return HttpResponse(status=400)

    event_type = event['type']
    logger.info(f"📩 Stripe webhook received: {event_type}")

    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        email = session['customer_details']['email']
        stripe_customer_id = session['customer']
        stripe_subscription_id = session.get('subscription')
        metadata = session.get('metadata', {})

        first_name = metadata.get('first_name', '')
        password = metadata.get('password')

        user = User.objects.filter(email=email).first()

        if not user and password:
            # Email/password signup (presignup)
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                password=password,
                is_active=True,
            )
            logger.info(f"🆕 Created user from webhook: {email}")

        elif user and not user.is_active:
            # OAuth signup – user was created by Allauth but is inactive until payment
            user.is_active = True
            user.save()
            logger.info(f"✅ Activated OAuth user from webhook: {email}")

        if user:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if not profile.stripe_customer_id:
                profile.stripe_customer_id = stripe_customer_id
            if not profile.stripe_subscription_id:
                profile.stripe_subscription_id = stripe_subscription_id
            if not profile.subscription_status:
                profile.subscription_status = 'trialing'
            if not profile.trial_end_date:
                # Only set a rough default — real trial_end will be updated on first invoice
                profile.trial_end_date = make_aware(datetime.now() + timedelta(days=14))
            profile.save()
            logger.info(f"✅ Trial info saved for {email} — customer ID: {stripe_customer_id}")
        else:
            logger.warning(f"⚠️ Could not create or find user for {email}")

    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription['customer']
        status = subscription['status']

        profile = UserProfile.objects.filter(stripe_customer_id=customer_id).first()
        if profile:
            profile.subscription_status = status
            profile.save()
            logger.info(f"🔁 Subscription updated: {customer_id} → {status}")

    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription['customer']

        profile = UserProfile.objects.filter(stripe_customer_id=customer_id).first()
        if profile:
            profile.subscription_status = 'canceled'
            profile.save()
            logger.info(f"❌ Subscription canceled: {customer_id}")

    elif event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice['customer']
        subscription_id = invoice.get('subscription')

        subscription = stripe.Subscription.retrieve(subscription_id) if subscription_id else None
        trial_end = datetime.fromtimestamp(subscription['trial_end']) if subscription and subscription['trial_end'] else None
        status = subscription['status'] if subscription else 'active'

        profile = UserProfile.objects.filter(stripe_customer_id=customer_id).first()
        if profile:
            profile.subscription_status = status
            profile.stripe_subscription_id = subscription_id
            if trial_end:
                profile.trial_end_date = make_aware(trial_end)
            profile.save()
            logger.info(
                f"💰 Payment succeeded: {customer_id} → status={status}, sub={subscription_id}, trial_end={trial_end}"
            )

    elif event_type == 'invoice.payment_failed':
        invoice = event['data']['object']
        customer_id = invoice['customer']

        profile = UserProfile.objects.filter(stripe_customer_id=customer_id).first()
        if profile:
            profile.subscription_status = 'past_due'
            profile.save()
            logger.warning(f"⚠️ Payment failed: {customer_id} → subscription past due")

    return HttpResponse(status=200)



@login_required
def cancel_subscription(request):
    try:
        profile = request.user.profile
        subscription_id = profile.stripe_subscription_id

        if not subscription_id:
            return JsonResponse({'success': False, 'error': 'No active subscription found.'}, status=400)

        # Cancel at period end to allow trial to run its course
        stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )

        # Optional: update local status immediately
        profile.subscription_status = 'canceled'
        profile.save()

        return JsonResponse({'success': True, 'message': 'Subscription canceled. It will remain active until the end of the trial or billing period.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def remove_meal(request):
    meal_id = request.POST.get('meal_id')
    meal_type = request.POST.get('meal_type')

    if not meal_id or not meal_type:
        return JsonResponse({'success': False, 'error': 'Missing meal ID or type'})

    try:
        meal = Meal.objects.get(id=meal_id)
        if meal_type == 'breakfast':
            meal.breakfast = None
        elif meal_type == 'lunch':
            meal.lunch = None
        elif meal_type == 'dinner':
            meal.dinner = None
        elif meal_type == 'snack':
            meal.snack = None
        else:
            return JsonResponse({'success': False, 'error': 'Invalid meal type'})

        meal.save()

        # Optional: trigger shopping list update logic here

        return JsonResponse({'success': True})
    except Meal.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Meal not found'})


def terms_view(request):
    return render(request, 'terms.html')

def privacy_view(request):
    return render(request, 'privacy.html')

@login_required
@require_POST
def update_exclude_purees(request):
    profile = request.user.profile
    profile.exclude_purees = request.POST.get("exclude_purees") == "on"
    profile.save()
    messages.success(request, "Puree preference updated.")
    return redirect('profile')

def contact(request):
    return render(request, 'contact.html')

def redirect_after_oauth_login(request):
    session_id = request.session.pop('oauth_checkout_session_id', None)

    if session_id:
        return redirect(f"https://checkout.stripe.com/c/{session_id}")
    
    # Just go to dashboard if no session (e.g., returning user)
    return redirect('dashboard')

def stripe_oauth_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('signup_cancelled')

    session = stripe.checkout.Session.retrieve(session_id)

    try:
        presignup = PreSignupSocial.objects.get(stripe_checkout_session_id=session_id)
    except PreSignupSocial.DoesNotExist:
        return redirect('signup_cancelled')

    User = get_user_model()
    user, created = User.objects.get_or_create(
        email=presignup.email,
        defaults={
            'username': presignup.email,
            'first_name': presignup.first_name,
            'is_active': True,  # Activate now that payment succeeded
        }
    )

    if not created and not user.is_active:
        user.is_active = True
        user.save()

    # ✅ Ensure UserProfile exists
    UserProfile.objects.get_or_create(user=user)

    # ✅ Link SocialAccount if not already linked
    if not SocialAccount.objects.filter(user=user, provider=presignup.provider).exists():
        if not SocialAccount.objects.filter(uid=presignup.uid, provider=presignup.provider).exists():
            SocialAccount.objects.create(
                user=user,
                uid=presignup.uid,
                provider=presignup.provider,
                extra_data={"email": presignup.email, "name": presignup.first_name},
            )

    # ✅ Clear session state
    request.session.pop('pending_sociallogin', None)
    request.session.pop('oauth_checkout_session_id', None)
    request.session['pixel_conversion_event'] = 'subscribe'

    # ✅ Log in user
    user.backend = 'allauth.account.auth_backends.AuthenticationBackend'
    login(request, user)

    return redirect('profile')

@require_POST
@csrf_exempt  # Optional if CSRF token is properly passed; safer to keep it enabled
def set_plan(request):
    try:
        data = json.loads(request.body)
        selected_plan = data.get("selected_plan", "monthly")
        request.session["selected_plan"] = selected_plan
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@login_required
def upgrade_required(request):
    return render(request, "upgrade_required.html", {
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    })


@login_required
def start_checkout(request):
    user = request.user
    logger.info("🔔 start_checkout triggered")
    logger.info("🔹 Request method: %s", request.method)
    logger.info("🔹 Headers: %s", dict(request.headers))
    logger.info("🔹 POST data: %s", request.POST)

    selected_plan = request.POST.get('selected_plan', 'monthly')

    price_id = settings.STRIPE_YEARLY_PRICE_ID if selected_plan == 'yearly' else settings.STRIPE_MONTHLY_PRICE_ID

    try:
        checkout_session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            customer_email=user.email,
            allow_promotion_codes=True,
            success_url=request.build_absolute_uri(reverse('profile')),
            cancel_url=request.build_absolute_uri(reverse('upgrade_required')),
            metadata={'user_id': str(user.id)},
        )

        logger.info("✅ Stripe checkout session created: %s", checkout_session.id)

        is_ajax = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
            request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        )

        logger.info("🔍 Is AJAX: %s", is_ajax)

        if is_ajax:
            return JsonResponse({'id': checkout_session.id})
        else:
            return redirect(checkout_session.url)

    except Exception as e:
        logger.exception("❌ Stripe checkout creation failed")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=400)
        return HttpResponse(str(e), status=400)

@login_required
def billing_portal(request):
    session = stripe.billing_portal.Session.create(
        customer=request.user.stripe_customer_id,
        return_url=request.build_absolute_uri(reverse('profile')),
    )
    return redirect(session.url)