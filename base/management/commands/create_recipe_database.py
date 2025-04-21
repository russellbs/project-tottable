import csv
import re
import json
import os
from openai import OpenAI

# Securely initialize the OpenAI client
client = OpenAI(api_key="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")

# ID Generators
recipe_counter = 0
ingredient_counter = 0
ingredient_map = {}  # name: ING-xxxxxxx

def next_recipe_id():
    global recipe_counter
    recipe_counter += 1
    return f"REC-{recipe_counter:07d}"

def next_ingredient_id():
    global ingredient_counter
    ingredient_counter += 1
    return f"ING-{ingredient_counter:07d}"

# Function to parse structured data using OpenAI
def parse_recipes(text):
    prompt = f"""
You are an expert pediatric nutritionist writing structured baby-food recipes for new parents. Rewrite the provided recipe completely, adhering strictly to the following detailed guidelines to match the provided examples closely:

### General Style:
- Use a warm, supportive, and nutrition-focused tone.
- Clearly highlight key nutritional benefits relevant to the baby's age.
- Include descriptive words that enhance appeal ("smooth," "creamy," "nutrient-rich," "naturally sweet," "vibrant," "comforting," etc.).
- Keep the description concise but informative, typically one short sentence that highlights texture, main ingredients, and nutritional benefits.

### Ingredients:
- Clearly list each ingredient by name, without extra adjectives.
- Quantities and units must be simple, clear, and appropriate for baby recipes.

### Instructions:
- Break down the instructions clearly into distinct steps (around 3–5 steps).
- Each step should have a brief descriptive heading followed by detailed instructions (e.g., "Cook the Rice: Simmer rice until tender...").
- Always specify clear cooking methods (steaming, boiling, baking) with precise timings.
- Include helpful notes for adjusting textures (e.g., adding water or breast milk if too thick) suitable for babies’ age groups.
- Write in a supportive and practical tone to guide new parents.

### Tottable Tips:
- Provide 2-3 actionable tips directly related ONLY to ingredients or preparation methods.
- Avoid mentioning serving suggestions, storage duration, or unrelated nutritional facts.
- Examples of appropriate tips:
  - Suggest easy batch-preparation ideas ("Prepare Ahead: Blend oats into powder and store in airtight containers").
  - Provide ways to adjust flavors or textures for different developmental stages ("Texture Progression: Mash coarsely or serve small soft pieces as your baby grows").
  - Recommend family-friendly variations for convenience ("Family-Friendly Option: Use leftovers as a side dish for adults").

### Response Format (JSON):
Respond ONLY with a JSON array containing exactly one object with these keys filled out precisely like the examples provided:

[
  {{
    "recipe_id": "REC-xxxxxxx",
    "title": "Concise, appealing title highlighting main ingredients",
    "description": "Short, appealing sentence highlighting texture, ingredients, and nutritional benefit.",
    "min_age": NUMBER,
    "meal_type": ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"],
    "prep_time_min": NUMBER,
    "cook_time_min": NUMBER,
    "ingredients": [
      {{
        "ingredient_id": "",
        "name": "Ingredient Name",
        "quantity": "Number or simple fraction",
        "unit": "Clear cooking measurement (cups, tbsp, tsp, medium, etc.)"
      }}
    ],
    "instructions": [
      "Step 1: Brief descriptive heading: clear, detailed instruction.",
      "Step 2: Brief descriptive heading: clear, detailed instruction."
    ],
    "tottable_tips": [
      "First practical, preparation-focused tip.",
      "Second practical, ingredient-focused tip.",
      "Third optional practical tip (if applicable)."
    ]
  }}
]

### Provided Examples (Match this style exactly):

Example 1:
Title: Baby Oatmeal  
Description: Smooth, nutrient-rich oatmeal made from finely ground oats. Perfect for introducing grains to babies.  
Tottable Tips: "Prepare Ahead: Blend oats into powder for quick use."; "Add Flavor: Stir in fruit puree as your baby grows."

Example 2:
Title: Cozy Apple-Pear Puree  
Description: A smooth and naturally sweet puree made with apples and pears, packed with healthy carbohydrates and vitamin C.  
Tottable Tips: "Mix it Up: Combine puree with rice cereal or oatmeal for added texture."; "Batch Cooking: Double recipe and freeze small portions for convenience."

Example 3:
Title: Sweet Summer Greens Puree  
Description: A vibrant, nutrient-rich puree made with sweet green peas, tender zucchini, and a hint of fresh mint. Perfect for babies starting their solids journey.  
Tottable Tips: "Texture Progression: Blend to desired smoothness or leave slightly chunkier as your baby advances."; "Ingredient Swap: Substitute spinach for zucchini for added nutrition."

### Important:
- Match these examples exactly in tone, style, and structure.
- Respond ONLY in the requested structured JSON format.

Provided Recipe to Rewrite:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    return json.loads(content)


# Main script
with open('recipes.txt', 'r', encoding='utf-8') as file:
    raw_text = file.read()

recipes_raw = [r.strip() for r in re.split(r'-{3,}', raw_text) if r.strip()]

with open('recipes.csv', 'w', newline='', encoding='utf-8') as rec_file, \
     open('ingredients.csv', 'w', newline='', encoding='utf-8') as ing_file, \
     open('recipe_ingredients.csv', 'w', newline='', encoding='utf-8') as rec_ing_file:

    recipe_writer = csv.writer(rec_file)
    ingredient_writer = csv.writer(ing_file)
    recipe_ingredient_writer = csv.writer(rec_ing_file)

    recipe_writer.writerow(['Recipe ID', 'Title', 'Description', 'Min Age (Months)',
                            'Meal Type', 'Prep Time (min)', 'Cook Time (min)',
                            'Instructions', 'Tottable Tips'])

    ingredient_writer.writerow(['Ingredient ID', 'Name', 'Food Category',
                                'Allergen Type', 'Is Vegetarian', 'Is Vegan'])

    recipe_ingredient_writer.writerow(['Recipe ID', 'Ingredient ID', 'Quantity', 'Unit'])

    recipes_array = parse_recipes(raw_text)  # Parse all recipes at once

    for data in recipes_array:
        recipe_id = data["recipe_id"]

        recipe_writer.writerow([
            recipe_id,
            data['title'],
            data['description'],
            data['min_age'],
            "; ".join(data['meal_type']),
            data['prep_time_min'],
            data['cook_time_min'],
            "\n".join(data['instructions']),
            data['tottable_tips']
        ])

        for ing in data['ingredients']:
            ing_name = ing['name'].strip().lower()

            if ing_name not in ingredient_map:
                ingredient_id = next_ingredient_id()
                ingredient_map[ing_name] = ingredient_id

                cat_prompt = f"""
Categorize this ingredient in JSON format:

Ingredient: {ing_name}

Return exactly these fields:
{{
    "Food Category": "",
    "Allergen Type": "",
    "Is Vegetarian": true/false,
    "Is Vegan": true/false
}}

Respond ONLY in valid JSON format.
"""
                cat_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": cat_prompt}],
                    temperature=0,
                )
                cat_data = json.loads(cat_response.choices[0].message.content.strip())

                ingredient_writer.writerow([
                    ingredient_id,
                    ing['name'],
                    cat_data['Food Category'],
                    cat_data['Allergen Type'],
                    cat_data['Is Vegetarian'],
                    cat_data['Is Vegan']
                ])
            else:
                ingredient_id = ingredient_map[ing_name]

            recipe_ingredient_writer.writerow([
                recipe_id,
                ingredient_id,
                ing['quantity'],
                ing['unit']
            ])

print("Recipes and ingredients have been successfully parsed and saved!")
