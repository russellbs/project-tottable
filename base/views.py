from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Sum
from .models import Ingredient, Child, Recipe, MealPlan, Meal, RecipeIngredient
from .forms import AddChildForm, WithinWeekPreferencesForm, AcrossWeekPreferencesForm, SignupForm  # Import the AddChildForm
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
import logging
import random
from datetime import timedelta

def landing_page(request):
    return render(request, 'landing.html')

# View for displaying the user's profile and handling the Add Child and UserPreferences Forms
@login_required
def profile(request):
    user = request.user
    ingredients = Ingredient.objects.all()
    children = Child.objects.filter(parent=user)

    profile = user.profile

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

    context = {
        "user": user,
        "ingredients": ingredients,
        "children": children,
        "within_week_preferences_flat": within_week_preferences_flat,
        "across_week_preferences_flat": across_week_preferences_flat,
    }

    return render(request, "profile.html", context)

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

            # Return JSON response
            return JsonResponse({
                'success': True,  # Added this key
                'name': child.name,
                'dob': child.dob.strftime('%Y-%m-%d'),
                'likes_ingredients': list(child.likes_ingredients.values_list('name', flat=True)),
                'dislikes_ingredients': list(child.dislikes_ingredients.values_list('name', flat=True)),
                'allergies': child.allergies or '',
            })
        except Exception as e:
            print(f"Error in add_child view: {e}")  # Log the error
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
def dashboard(request):
    user = request.user
    children = Child.objects.filter(parent=user)

    # Account creation date
    account_creation_date = user.date_joined.date()

    # Determine the start of the week containing the account creation date
    account_creation_week_start = account_creation_date - timedelta(days=account_creation_date.weekday())

    # Determine the week to display (default: current week)
    week_offset = int(request.GET.get('week', 0))
    current_week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
    displayed_week_start = current_week_start + timedelta(weeks=week_offset)
    displayed_week_end = displayed_week_start + timedelta(days=6)
    previous_week_start = displayed_week_start - timedelta(days=7)

    # Allow "Next Week" 3 days before the current week ends
    next_week_available_date = current_week_start + timedelta(days=4)  # Thursday of the current week

    # Calculate the next week's start date
    next_week_start = displayed_week_start + timedelta(days=7)

    # Prepare meal plans
    meal_plans = []
    for child in children:
        latest_meal_plan = MealPlan.objects.filter(
            child=child,
            start_date=displayed_week_start,
            end_date=displayed_week_end,
        ).order_by('-created_at').first()  # Ensure we fetch the latest meal plan

        if latest_meal_plan:
            print(f"Dashboard displaying Meal Plan ID: {latest_meal_plan.id}, Created At: {latest_meal_plan.created_at}")
        else:
            print(f"No meal plan found for {child.name} for this week. Generating a new one...")

        # Generate meal plan only if none exists
        if not latest_meal_plan:
            latest_meal_plan = generate_meal_plan(child.id)

        meal_plans.append((child, latest_meal_plan))

    context = {
        'children': children,
        'meal_plans': meal_plans,
        'displayed_week_start': displayed_week_start,
        'displayed_week_end': displayed_week_end,
        'previous_week_start': previous_week_start,
        'next_week_start': next_week_start,  # Pass this to the template
        'next_week_available_date': next_week_available_date,
        'week_offset': week_offset,
        'account_creation_date': account_creation_date,
        'account_creation_week_start': account_creation_week_start,
    }
    
    return render(request, 'dashboard.html', context)




@login_required
def meal_plan(request):
    # Placeholder context
    context = {}
    return render(request, 'meal_plan.html', context)

@login_required
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

    # Pagination
    paginator = Paginator(recipes.distinct(), 12)  # Show 12 recipes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'recipe_library.html', {
        'page_obj': page_obj,
        'query': query,
        'meal_type': meal_type,
        'age_range': age_range,
        'swap_mode': swap_mode,
        'day': day,
    })

@login_required
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

    return render(request, 'recipe_detail.html', {
        'recipe': recipe,
        'instructions': instructions,
        'swap_mode': swap_mode,
        'meal_type': meal_type,
        'day': day,
        'back_link_url': back_link_url,
    })

def generate_meal_plan(child_id):
    from datetime import timedelta

    # Fetch child and relevant preferences
    child = get_object_or_404(Child, id=child_id)
    dislikes = child.dislikes_ingredients.all()
    likes = child.likes_ingredients.all()
    allergies = child.allergies.split(',') if child.allergies else []

    # Fetch preferences
    profile = child.parent.profile

    # Define the days and meal types
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    # Check if a meal plan for the current week already exists
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    meal_plan, created = MealPlan.objects.get_or_create(
        child=child, start_date=start_date, end_date=end_date
    )

    if not created:
        # If a meal plan already exists, do nothing
        return meal_plan

    # Variety mapping (normalize to lowercase for consistency)
    variety_levels = [
        ("high", (6, 7)),
        ("medium", (4, 5)),
        ("low", (2, 3)),
        ("no", (1, 1)),  # No Variety
    ]

    # Assign recipes for each meal type
    for meal_type in ["Breakfast", "Lunch", "Dinner", "Snack"]:
        # Normalize the preferred variety to lowercase
        preferred_level = profile.within_week_preferences.get(meal_type.lower(), "medium").lower()

        # Initialize variables
        selected_recipes = []
        fallback_index = next((i for i, (level, _) in enumerate(variety_levels) if level == preferred_level), None)

        if fallback_index is None:
            print(f"Warning: Unrecognized variety level '{preferred_level}', defaulting to 'medium'.")
            fallback_index = 1  # Default to "medium"

        # Try each variety level, starting from the preferred level
        while fallback_index < len(variety_levels):
            variety_name, (min_recipes, max_recipes) = variety_levels[fallback_index]
            num_unique_recipes = random.randint(min_recipes, max_recipes)

            # Fetch and shuffle recipes
            possible_recipes = list(
                Recipe.objects.filter(
                    meal_types__name=meal_type
                ).exclude(
                    ingredients__in=dislikes
                ).exclude(
                    ingredients__food_category__in=allergies
                )
            )

            if len(possible_recipes) >= num_unique_recipes:
                # We have enough recipes for this variety level
                selected_recipes = possible_recipes[:num_unique_recipes]
                break
            else:
                # Try the next lower variety level
                fallback_index += 1

        # If still no recipes are found, skip this meal type
        if not selected_recipes:
            print(f"No suitable recipes found for meal type {meal_type}! Skipping...")
            continue

        # Assign meals for each day
        for day_index, day in enumerate(days):
            if variety_name == "no":
                # Use the same recipe every day
                selected_recipe = selected_recipes[0]
            else:
                # Rotate through selected recipes for variety
                selected_recipe = selected_recipes[day_index % len(selected_recipes)]

            # Create or update the meal for the day
            meal, _ = Meal.objects.get_or_create(
                meal_plan=meal_plan,
                day=day,
                defaults={meal_type.lower(): selected_recipe},
            )
            # Update the meal in case it already exists but doesn't have the current meal_type
            setattr(meal, meal_type.lower(), selected_recipe)
            meal.save()

    return meal_plan


logger = logging.getLogger(__name__)

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
        profile.save()

        # Return updated preferences in the response
        return JsonResponse({"success": True, "preferences": preferences})
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
        possible_recipes = list(
            Recipe.objects.filter(meal_types__name=meal_type)
            .exclude(ingredients__in=dislikes)
            .exclude(ingredients__food_category__in=allergies)
        )

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
            else:
                # Ensure meals repeat for consecutive days
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

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.username = user.email  # Use email as username
            user.save()
            login(request, user)  # Log in the user immediately
            return redirect("dashboard")  # Redirect to dashboard after signup
    else:
        form = SignupForm()
    return render(request, "signup.html", {"form": form})

