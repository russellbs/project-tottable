import openai
import pandas as pd
import json
import re
import os

# 🔹 Load existing ingredients (if available) to prevent duplicate IDs
try:
    df_ingredients = pd.read_csv("ingredients.csv")
    existing_ingredients = df_ingredients.set_index("name").to_dict(orient="index")
except FileNotFoundError:
    existing_ingredients = {}

# 🔹 Load existing recipes to maintain correct numbering
try:
    df_recipes = pd.read_csv("recipes.csv")
    if not df_recipes.empty:
        last_recipe_id = int(df_recipes.iloc[-1]["recipe_id"].replace("REC-", ""))
    else:
        last_recipe_id = 0
except (FileNotFoundError, KeyError):
    last_recipe_id = 0

# 🔹 Function to assign or reuse Ingredient IDs
def get_ingredient_id(name):
    """Assigns a unique ingredient ID if not already assigned."""
    if name in existing_ingredients:
        return existing_ingredients[name]["Ingredient ID"]
    else:
        new_id = f"ING-{len(existing_ingredients) + 1:07d}"
        existing_ingredients[name] = {"Ingredient ID": new_id, "name": name}
        return new_id

# 🔹 Function to read recipes and detect sections (age categories)
def load_recipes_with_sections(filename):
    """Reads a TXT file and extracts recipes grouped by age category."""
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    recipes = []
    current_section = None
    current_recipe = []

    for line in lines:
        line = line.strip()

        # Detect section headers (e.g., "### Meals Starting at 6 Months")
        if line.startswith("###"):
            current_section = line.replace("###", "").strip()
            continue

        # New recipe starts when there's a "---" separator
        if line == "---":
            if current_recipe:
                recipes.append({"section": current_section, "raw_text": "\n".join(current_recipe)})
                current_recipe = []
            continue

        # Add recipe lines to current recipe
        current_recipe.append(line)

    # Add last recipe (if any)
    if current_recipe:
        recipes.append({"section": current_section, "raw_text": "\n".join(current_recipe)})

    return recipes

# 🔹 Extract ingredients from a recipe
def extract_ingredients(recipe_text):
    """Extracts ingredients from the raw text by identifying properly formatted lines."""
    ingredients = []
    lines = recipe_text.split("\n")

    for line in lines:
        line = line.strip()

        # Detect ingredients: Start with a number or fraction (e.g., "¼ cup water", "1 medium zucchini")
        if re.match(r"^\d+|^\d+/\d+", line):
            parts = line.split(" ", 2)  # Split into quantity, unit, and ingredient name
            
            if len(parts) < 2:
                continue  # Skip malformed lines

            quantity = parts[0].strip()  # First part is always the quantity
            
            if len(parts) == 2:
                name = parts[1].strip()  # If only two parts, assume no unit (e.g., "1 zucchini")
                unit = ""
            else:
                unit = parts[1].strip()  # Second part is the unit
                name = parts[2].strip()  # Third part is the ingredient name
            
            # Assign a unique ingredient ID
            ingredient_id = get_ingredient_id(name)

            # Store structured ingredient data
            ingredients.append({
                "ingredient_id": ingredient_id,
                "name": name,
                "quantity": quantity,
                "unit": unit
            })
    
    return ingredients

# 🔹 Convert a batch of recipes into OpenAI's structured format
def process_batch(batch, start_recipe_id):
    """Sends a batch of recipes to OpenAI and ensures correct JSON format."""
    global existing_ingredients  

    # Assign Recipe IDs properly
    for index, recipe in enumerate(batch):
        recipe["recipe_id"] = f"REC-{(start_recipe_id + index):07d}"
        recipe["ingredients"] = extract_ingredients(recipe["raw_text"])

    # 🔹 OpenAI API Call
    batch_prompt = json.dumps(batch, indent=2)

    client = openai.OpenAI(api_key="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")

    print("\n🔹 Sending API Request...")
    print(f"🔸 Sending batch with {len(batch)} recipes to OpenAI...\n")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                    "You are an expert in structuring baby food recipes for a meal-planning database called Tottable. "
                    "Tottable helps parents prepare nutritious meals for their babies by offering structured recipes "
                    "that focus on developmental nutrition, ingredient benefits, and easy preparation.\n"
                    "\n"
                    "Your job is to convert raw recipes into a structured JSON format, following these rules:\n"
                    "- **Return a JSON array of recipe objects.**\n"
                    "- Each recipe must include: 'recipe_id', 'title', 'description', 'min_age', 'meal_type', 'prep_time', 'cook_time', 'ingredients', 'instructions', and 'tags'.\n"
                    "- Ingredients must be structured as: 'ingredient_id', 'name', 'quantity', 'unit'.\n"
                    "- **The output must be a JSON array.** Do not return a single object.\n"
                    "- The **instructions must be formatted as a JSON array**, where each cooking step is a separate string in the list.\n"
                    "- The **instructions must be fully paraphrased** in clear, simple, and natural language. "
                    "Do NOT just rearrange words—rewrite them while keeping the meaning intact.\n"
                    "- Ensure the recipe is correctly categorized under the given age group.\n"
                    "- Add a 'Tottable Tip'—focus ONLY on the ingredients and preparation in the recipe. "
                    "Do NOT suggest pairings, serving ideas, or additional ingredients. "
                    "Instead, highlight preparation techniques, consistency adjustments, or nutritional benefits of ingredients already present.\n"
                    "- Ensure the tone is warm, supportive, and research-backed, similar to expert advice from a pediatric nutritionist.\n"
                    "- Do NOT include storage instructions or book citations—this should be an original reformatted recipe."
                },
                {"role": "user", "content": batch_prompt}
            ]
        )

        # ✅ **Print the OpenAI response for debugging**
        print("\n🔹 Raw OpenAI Response:")
        print(response)

        response_content = response.choices[0].message.content.strip()

        # ✅ **Check if the response is empty**
        if not response_content:
            print("❌ OpenAI returned an empty response!")
            return []

        # ✅ **Ensure JSON format is clean**
        if response_content.startswith("```json"):
            response_content = response_content[7:]  
        if response_content.endswith("```"):
            response_content = response_content[:-3]

        # ✅ **Convert to JSON**
        try:
            structured_response = json.loads(response_content)

            # ✅ **Ensure response is always a list**
            if isinstance(structured_response, dict):  
                structured_response = [structured_response]  

            return structured_response

        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parsing Error: {e}")
            print("⚠️ The response might still have formatting issues. Printing raw response again:\n", response_content)
            return []

    except Exception as e:
        print(f"\n❌ Error processing batch: {e}")
        return []

# 🔹 Save structured data
def save_to_csv(data, filename):
    df = pd.DataFrame(data)
    df.to_csv(filename, mode="a", index=False, header=not os.path.exists(filename))

# 🔹 Main Processing Function
def process_recipes(filename, batch_size=250):
    """Processes recipes in batches and saves structured output."""
    
    raw_recipes = load_recipes_with_sections(filename)
    structured_recipes = []
    recipe_ingredients_data = []

    # ✅ Load existing recipes to continue numbering correctly
    try:
        df_recipes = pd.read_csv("recipes.csv")
        if not df_recipes.empty:
            last_recipe_id = int(df_recipes.iloc[-1]["recipe_id"].replace("REC-", ""))
        else:
            last_recipe_id = 0
    except (FileNotFoundError, KeyError):
        last_recipe_id = 0

    for i in range(0, len(raw_recipes), batch_size):
        batch = raw_recipes[i:i+batch_size]
        print(f"\n🚀 Processing batch {i // batch_size + 1}/{len(raw_recipes) // batch_size + 1}...")

        # ✅ Pass the correct `start_recipe_id`
        structured_batch = process_batch(batch, last_recipe_id + 1)

        if structured_batch:
            structured_recipes.extend(structured_batch)

            # ✅ Extract and store recipe-ingredient relationships
            for recipe in structured_batch:
                recipe_id = recipe["recipe_id"]
                for ingredient in recipe["ingredients"]:
                    recipe_ingredients_data.append({
                        "recipe_id": recipe_id,
                        "ingredient_id": ingredient["ingredient_id"],
                        "quantity": ingredient["quantity"],
                        "unit": ingredient["unit"]
                    })

            # ✅ Save to files
            save_to_csv(structured_batch, "recipes.csv")
            save_to_csv(recipe_ingredients_data, "recipe_ingredients.csv")

            # ✅ Save updated `ingredients.csv` with unique names
            save_to_csv([{"Ingredient ID": v["Ingredient ID"], "name": v["name"]} for v in existing_ingredients.values()], "ingredients.csv")

            # ✅ Update last_recipe_id for the next batch
            last_recipe_id += len(batch)

        else:
            print("⚠️ No structured recipes returned from OpenAI.")

    print("\n✅ All recipes processed successfully!")

# 🔹 Run the script
process_recipes("recipes.txt", batch_size=250)
