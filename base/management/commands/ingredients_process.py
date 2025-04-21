import pandas as pd
import ast

# Load recipes CSV file
df_recipes = pd.read_csv("recipes.csv")

# Initialize a dictionary to store unique ingredients
ingredients_dict = {}

# Iterate over the ingredients column
for index, row in df_recipes.iterrows():
    try:
        # Parse the ingredients column from string to list of dictionaries
        ingredient_list = ast.literal_eval(row["ingredients"])

        for ingredient in ingredient_list:
            ingredient_id = ingredient["ingredient_id"]
            name = ingredient["name"].strip().lower()  # Normalize names to avoid duplicates

            # Store in dictionary to ensure uniqueness
            if ingredient_id not in ingredients_dict:
                ingredients_dict[ingredient_id] = {"Ingredient ID": ingredient_id, "name": name}

    except (ValueError, SyntaxError):
        print(f"Skipping row {index} due to parsing error.")

# Convert the dictionary to a DataFrame
df_ingredients = pd.DataFrame.from_dict(ingredients_dict, orient="index")

# Save to ingredients.csv
df_ingredients.to_csv("ingredients_process.csv", index=False)

print("✅ Ingredients successfully extracted and saved to ingredients.csv.")
