from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .models import Ingredient, Child, Recipe, MealPlan, Meal
from .forms import AddChildForm, WithinWeekPreferencesForm, AcrossWeekPreferencesForm  # Import the AddChildForm
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
import logging
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
        {"meal": meal, "value": profile.within_week_preferences.get(meal, "No preference selected").title()}
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
        meal_plan = MealPlan.objects.filter(
            child=child,
            start_date=displayed_week_start,
            end_date=displayed_week_end,
        ).first()
        if not meal_plan:
            meal_plan = generate_meal_plan(child.id)
        meal_plans.append((child, meal_plan))

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

    # Define the days and meal types
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    # Create a new MealPlan
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=6)
    meal_plan = MealPlan.objects.create(
        child=child,
        start_date=start_date,
        end_date=end_date,
    )

    # Populate the meals for each day
    for day in days:
        breakfast = Recipe.objects.filter(
            meal_types__name='Breakfast'
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__food_category__in=allergies
        ).order_by('?').first()

        lunch = Recipe.objects.filter(
            meal_types__name='Lunch'
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__food_category__in=allergies
        ).order_by('?').first()

        dinner = Recipe.objects.filter(
            meal_types__name='Dinner'
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__food_category__in=allergies
        ).order_by('?').first()

        snack = Recipe.objects.filter(
            meal_types__name='Snack'
        ).exclude(
            ingredients__in=dislikes
        ).exclude(
            ingredients__food_category__in=allergies
        ).order_by('?').first()

        # Create the meal for this day
        Meal.objects.create(
            meal_plan=meal_plan,
            day=day,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            snack=snack,
        )

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
    profile = request.user.profile

    if request.method == 'POST':
        print("POST Data Received:", request.POST)  # Log the data
        form = WithinWeekPreferencesForm(request.POST)
        if form.is_valid():
            form.save(profile)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                preferences = {
                    "breakfast": profile.within_week_preferences.get("breakfast", "No preference selected"),
                    "lunch": profile.within_week_preferences.get("lunch", "No preference selected"),
                    "dinner": profile.within_week_preferences.get("dinner", "No preference selected"),
                    "snack": profile.within_week_preferences.get("snack", "No preference selected"),
                }
                return JsonResponse({"success": True, "preferences": preferences})

            messages.success(request, "Within-week preferences updated successfully!")
            return redirect("profile")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": "Invalid form submission."}, status=400)

            messages.error(request, "Please correct the errors below.")

    initial_data = {
        "meal_variety_breakfast": profile.within_week_preferences.get("breakfast", "medium"),
        "meal_variety_lunch": profile.within_week_preferences.get("lunch", "medium"),
        "meal_variety_dinner": profile.within_week_preferences.get("dinner", "medium"),
        "meal_variety_snack": profile.within_week_preferences.get("snack", "medium"),
    }
    form = WithinWeekPreferencesForm(initial=initial_data)
    return render(request, "update_preferences.html", {"form": form})


@login_required
def update_across_week_preferences(request):
    profile = request.user.profile

    if request.method == 'POST':
        print("POST Data Received:", request.POST)  # Log the data
        form = AcrossWeekPreferencesForm(request.POST)
        if form.is_valid():
            form.save(profile)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                # Return all meal types for Across-Weeks preferences
                preferences = {
                    "breakfast": profile.across_week_preferences.get("breakfast", "No preference selected"),
                    "lunch": profile.across_week_preferences.get("lunch", "No preference selected"),
                    "dinner": profile.across_week_preferences.get("dinner", "No preference selected"),
                    "snack": profile.across_week_preferences.get("snack", "No preference selected"),
                }
                return JsonResponse({"success": True, "preferences": preferences})

            messages.success(request, "Across-week preferences updated successfully!")
            return redirect("profile")
        else:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": "Invalid form submission."}, status=400)

            messages.error(request, "Please correct the errors below.")

    initial_data = {
        "breakfast": profile.across_week_preferences.get("breakfast", "medium"),
        "lunch": profile.across_week_preferences.get("lunch", "medium"),
        "dinner": profile.across_week_preferences.get("dinner", "medium"),
        "snack": profile.across_week_preferences.get("snack", "medium"),
    }
    form = AcrossWeekPreferencesForm(initial=initial_data)
    return render(request, "update_preferences.html", {"form": form})


