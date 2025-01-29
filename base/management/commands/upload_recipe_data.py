import csv
from django.core.management.base import BaseCommand
from base.models import Ingredient, Recipe, RecipeIngredient, MealType
from fractions import Fraction

class Command(BaseCommand):
    help = "Upload recipe data from CSV files into the database"

    def handle(self, *args, **kwargs):
        # Paths to your data files
        base_path = '/Users/benjaminrussell/Documents/Project Tottable/data'
        ingredients_file = f'{base_path}/Ingredients.csv'
        recipes_file = f'{base_path}/Recipes.csv'
        recipe_ingredients_file = f'{base_path}/Recipe_Ingredients.csv'

        # Upload Ingredients
        self.stdout.write("Uploading ingredients...")
        with open(ingredients_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ingredient, created = Ingredient.objects.update_or_create(
                    id=row['Ingredient ID'],  # Use string-based IDs
                    defaults={
                        'name': row['Name'],
                        'food_category': row['Food Category'],
                        'allergen_type': row['Allergen Type'],
                        'is_vegetarian': row['Is Vegetarian'].strip() == 'True',
                        'is_vegan': row['Is Vegan'].strip() == 'True',
                    }
                )
                if created:
                    self.stdout.write(f"Added ingredient: {ingredient.name}")

        # Upload Recipes
        self.stdout.write("Uploading recipes...")
        with open(recipes_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Fetch or create meal types (if meal_types is ManyToManyField)
                meal_type_names = [name.strip() for name in row['Meal Type'].split(';') if name]
                meal_types = [MealType.objects.get_or_create(name=name)[0] for name in meal_type_names]

                recipe, created = Recipe.objects.update_or_create(
                    id=row['Recipe ID'],  # Use string-based IDs
                    defaults={
                        'title': row['Title'],
                        'description': row['Description'],
                        'preparation_time': int(row['Prep Time (min)']),
                        'cooking_time': int(row['Cook Time (min)']),
                        'instructions': row['Instructions'],
                        'tags': row['Tags'],
                        'image': row['Image URL'],
                        'min_age_months': int(row['Min Age (Months)']),
                        'max_age_months': int(row.get('Max Age (Months)', 24)),
                        'tips': row['Tottable Tips'],  # Add Tottable Tips here
                    }
                )
                # Assign meal types if ManyToManyField
                if created:
                    recipe.meal_types.set(meal_types)
                    self.stdout.write(f"Added recipe: {recipe.title}")

        # Upload RecipeIngredients
        self.stdout.write("Uploading recipe ingredients...")
        with open(recipe_ingredients_file, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    recipe = Recipe.objects.get(id=row['Recipe ID'])  # Match string IDs
                    ingredient = Ingredient.objects.get(id=row['Ingredient ID'])  # Match string IDs

                    # Convert quantity to fraction if possible
                    quantity = row['Quantity']
                    try:
                        numeric_quantity = float(quantity)
                        fraction_quantity = str(Fraction(numeric_quantity).limit_denominator(8))
                    except ValueError:
                        fraction_quantity = quantity  # Use original value if not numeric

                    recipe_ingredient, created = RecipeIngredient.objects.update_or_create(
                        recipe=recipe,
                        ingredient=ingredient,
                        defaults={
                            'quantity': fraction_quantity,
                            'unit': row.get('Unit', ''),  # Include unit from CSV (use empty string if missing)
                        }
                    )
                    if created:
                        self.stdout.write(f"Added recipe ingredient: {ingredient.name} for {recipe.title}")
                except Recipe.DoesNotExist:
                    self.stderr.write(f"Recipe with ID {row['Recipe ID']} not found.")
                except Ingredient.DoesNotExist:
                    self.stderr.write(f"Ingredient with ID {row['Ingredient ID']} not found.")

        # Update `is_vegetarian` and `is_vegan` for Recipes
        self.stdout.write("Updating recipe dietary information...")
        recipes = Recipe.objects.all()
        for recipe in recipes:
            ingredients = recipe.ingredients.all()
            is_vegetarian = all(ingredient.is_vegetarian for ingredient in ingredients)
            is_vegan = all(ingredient.is_vegan for ingredient in ingredients)
            recipe.is_vegetarian = is_vegetarian
            recipe.is_vegan = is_vegan
            recipe.save()

        self.stdout.write("Data upload completed.")
