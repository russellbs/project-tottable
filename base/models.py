from django.db import models
from django.contrib.auth.models import User
from fractions import Fraction

def default_meal_variety():
    return {
        "breakfast": "medium",
        "lunch": "medium",
        "dinner": "medium",
        "snack": "medium",
    }

def default_within_week_preferences():
    """Default within-week preferences for each meal type."""
    return {
        "breakfast": "medium",
        "lunch": "medium",
        "dinner": "medium",
        "snack": "medium",
    }

def default_across_week_preferences():
    """Default across-week preferences for each meal type."""
    return {
        "breakfast": "medium",
        "lunch": "medium",
        "dinner": "medium",
        "snack": "medium",
    }

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    MEAL_VARIETY_CHOICES = [
        ('no', 'No Variety'),
        ('low', 'Low Variety'),
        ('medium', 'Medium Variety'),
        ('high', 'High Variety'),
    ]

    # Preferences for meal variety within a week
    within_week_preferences = models.JSONField(
        default=default_within_week_preferences,
        help_text="Meal variety preferences within a week for each meal type.",
    )

    # Preferences for meal variety across weeks
    across_week_preferences = models.JSONField(
        default=default_across_week_preferences,
        help_text="Meal variety preferences across weeks for each meal type.",
    )

    def get_within_week_display(self, meal_type):
        """Return display value for within-week preferences."""
        value = self.within_week_preferences.get(meal_type, "medium")
        return dict(self.MEAL_VARIETY_CHOICES).get(value, "No preference selected")

    def get_across_week_display(self, meal_type):
        """Return display value for across-week preferences."""
        value = self.across_week_preferences.get(meal_type, "medium")
        return dict(self.MEAL_VARIETY_CHOICES).get(value, "No preference selected")


### Ingredient Model with Food Category ###
class Ingredient(models.Model):
    id = models.CharField(max_length=15, primary_key=True)  # Use string IDs
    name = models.CharField(max_length=100)
    food_category = models.CharField(max_length=100, help_text="Category of the ingredient (e.g., Fruit, Meat, Vegetables, Grains)")
    allergen_type = models.CharField(max_length=100, blank=True, null=True, help_text="Type of allergen, if applicable (e.g., Nuts, Dairy, Gluten)")
    is_vegetarian = models.BooleanField(default=True)
    is_vegan = models.BooleanField(default=True)

    def __str__(self):
        return self.name

### Recipe Model with Tags and Favorites ###
class Recipe(models.Model):
    id = models.CharField(max_length=15, primary_key=True)  # Use string IDs
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient')
    meal_types = models.ManyToManyField('MealType')  # Use descriptive meal types
    preparation_time = models.IntegerField(help_text="Time in minutes")
    cooking_time = models.IntegerField(help_text="Time in minutes")
    instructions = models.TextField()
    is_vegetarian = models.BooleanField(default=True)
    is_vegan = models.BooleanField(default=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags for the recipe (e.g., High Protein, Gluten-Free)")
    image = models.ImageField(upload_to='recipes/', null=True, blank=True)
    min_age_months = models.IntegerField(help_text="Minimum age in months for this recipe", default=6)
    max_age_months = models.IntegerField(help_text="Maximum age in months for this recipe", default=24)
    tips = models.TextField(blank=True, null=True, help_text="Tottable tips for this recipe")  # New field

    def __str__(self):
        return self.title

class MealType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

### RecipeIngredient Model ###
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100)  # Keep this as a string to handle various formats
    unit = models.CharField(max_length=50, blank=True, null=True)  # Unit for the quantity

    def quantity_as_fraction(self):
        try:
            # Convert the quantity to a fraction if it's numeric
            numeric_quantity = float(self.quantity)
            fraction_quantity = Fraction(numeric_quantity).limit_denominator(8)
            return str(fraction_quantity)
        except ValueError:
            # Return the quantity as is if it can't be converted
            return self.quantity

    def __str__(self):
        unit_display = f" {self.unit}" if self.unit else ""
        return f"{self.quantity_as_fraction()}{unit_display} {self.ingredient.name} for {self.recipe.title}"

### Child Model (Now Uses User) ###
class Child(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children')  # Still points to User as parent
    name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name="Date of Birth")
    likes_ingredients = models.ManyToManyField(Ingredient, related_name='liked_by_children', blank=True)
    dislikes_ingredients = models.ManyToManyField(Ingredient, related_name='disliked_by_children', blank=True)
    likes_recipes = models.ManyToManyField(Recipe, related_name='liked_by_children', blank=True)
    dislikes_recipes = models.ManyToManyField(Recipe, related_name='disliked_by_children', blank=True)
    allergies = models.CharField(max_length=255, blank=True, help_text="List known allergens for the child (e.g., Nuts, Dairy)")

    def __str__(self):
        return f"{self.name} ({self.parent.username})"

class MealPlan(models.Model):
    child = models.ForeignKey(
        'Child', 
        on_delete=models.CASCADE, 
        related_name='meal_plans',
        help_text="The child this meal plan is for"
    )
    start_date = models.DateField(help_text="Start date of the meal plan week")
    end_date = models.DateField(help_text="End date of the meal plan week")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Meal Plan for {self.child.name} ({self.start_date} - {self.end_date})"

class Meal(models.Model):
    meal_plan = models.ForeignKey(
        MealPlan, 
        on_delete=models.CASCADE, 
        related_name='meals',
        help_text="The meal plan this meal is part of",
        null=True  # Temporarily allow null values
    )
    day = models.CharField(
        max_length=10, 
        choices=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday'),
        ]
    )
    breakfast = models.ForeignKey(
        'Recipe', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='meal_breakfast'
    )
    lunch = models.ForeignKey(
        'Recipe', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='meal_lunch'
    )
    dinner = models.ForeignKey(
        'Recipe', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='meal_dinner'
    )
    snack = models.ForeignKey(
        'Recipe', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='meal_snack'
    )

    def __str__(self):
        return f"{self.day.capitalize()} Meal for {self.meal_plan.child.name if self.meal_plan else 'No Plan'}"