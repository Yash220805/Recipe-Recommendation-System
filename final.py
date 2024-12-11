import requests
import json
import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

CACHE_FILE = "cache.json"

def save_cache(data, filename=CACHE_FILE):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print("Cache saved successfully.")

def load_cache(filename=CACHE_FILE):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {}

def fetch_recipes(ingredient, api_key='1'):
    cache = load_cache()
    if ingredient in cache:
        print(f"Using cached data for ingredient: {ingredient}")
        return cache[ingredient]
    
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}&apiKey={api_key}"
    response = requests.get(url)
    print(f"API URL: {url}")
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 200:
        recipes = response.json().get('meals', [])
        cache[ingredient] = recipes
        save_cache(cache)
        return recipes
    else:
        print("Error fetching recipes:", response.status_code)
        return []

def save_preferences(preferences, filename="preferences.json"):
    with open(filename, 'w') as file:
        json.dump(preferences, file, indent=4)
    print("Preferences saved successfully.")

def load_preferences(filename="preferences.json"):
    preferences = {}
    preferences['dietary_preference'] = input("Enter your dietary preference (e.g., Vegetarian, Non-Vegetarian, Vegan): ")
    save_preferences(preferences)
    return preferences

# Keywords for dietary preferences
DIETARY_KEYWORDS = {
    "Vegetarian": ["paneer", "vegetarian", "veg"],
    "Non-Vegetarian": ["chicken", "beef", "pork", "fish"],
    "Vegan": ["vegan"]
}

# Simulate additional nutritional information
ADDITIONAL_NUTRITIONAL_DATA = {
    "52940": {"calories": 500, "protein": 35, "carbs": 50, "fat": 20},
    "52939": {"calories": 200, "protein": 10, "carbs": 30, "fat": 5},
    # Add more simulated data here...
}

def tag_recipes(recipes):
    tagged_recipes = []
    for recipe in recipes:
        for diet, keywords in DIETARY_KEYWORDS.items():
            if any(keyword in recipe['strMeal'].lower() for keyword in keywords):
                recipe['diet'] = diet
                break
        else:
            recipe['diet'] = "unknown"

        # Add simulated nutritional data
        nutritional_data = ADDITIONAL_NUTRITIONAL_DATA.get(recipe['idMeal'], {})
        recipe.update(nutritional_data)
        
        tagged_recipes.append(recipe)
    return tagged_recipes

def filter_recipes_by_preferences(recipes, preferences):
    filtered_recipes = []
    dietary_preference = preferences['dietary_preference'].strip().lower()

    print(f"User preferences: {preferences}")

    for recipe in recipes:
        recipe_diet = recipe.get('diet', 'unknown').strip().lower()
        print(f"Checking recipe: {recipe['strMeal']} - Diet: {recipe_diet}")

        if dietary_preference == recipe_diet:
            filtered_recipes.append(recipe)
    
    return filtered_recipes

def extract_recipe_details(tagged_recipes):
    seen_ids = set()  # Keep track of seen recipe IDs
    recipe_details = []
    for recipe in tagged_recipes:
        if recipe['idMeal'] not in seen_ids:
            print(f"Processing recipe: {recipe}")
            details = {
                "title": recipe.get('strMeal'),
                "image": recipe.get('strMealThumb'),
                "id": recipe.get('idMeal'),
                "diet": recipe.get('diet', 'unknown'),
                "calories": recipe.get('calories', 'N/A'),
                "protein": recipe.get('protein', 'N/A'),
                "carbs": recipe.get('carbs', 'N/A'),
                "fat": recipe.get('fat', 'N/A')
            }
            recipe_details.append(details)
            seen_ids.add(recipe['idMeal'])  # Mark this ID as seen
    print(f"Extracted Recipe Details: {recipe_details}")
    return recipe_details

def save_data(data, filename="recipes.json"):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print("Data saved successfully.")

def get_detailed_recipe_guide(recipe):
    # Create a prompt for the LLM
    prompt = f"Provide a detailed, step-by-step cooking guide for the following recipe:\n\nTitle: {recipe['title']}\n\nIngredients:\n[Ingredients Placeholder]\n\nInstructions: [Instructions Placeholder]\n"

    # LLM Configuration
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-70b-8192")

    # Generate the detailed guide using the updated method
    detailed_guide = llm.invoke(prompt)
    return detailed_guide

def main():
    api_key = '1'  # Test API key
    preferences = load_preferences()
    
    ingredients = input("Please enter the ingredients (comma-separated): ")

    ingredient_list = ingredients.split(',')
    all_recipes = []
    for ingredient in ingredient_list:
        recipes = fetch_recipes(ingredient.strip(), api_key)
        if recipes:
            all_recipes.extend(recipes)

    if all_recipes:
        tagged_recipes = tag_recipes(all_recipes)
        filtered_recipes = filter_recipes_by_preferences(tagged_recipes, preferences)
        print(f"Filtered Recipes: {filtered_recipes}")
        recipe_details = extract_recipe_details(filtered_recipes)
        save_data(recipe_details)  # Save data even if there are no filtered recipes
        save_preferences(preferences)  # Save preferences every time the code runs
        
        selected_recipe_title = input("Please enter the title of the recipe you want details for: ")
        for recipe in recipe_details:
            if recipe['title'].lower() == selected_recipe_title.lower():
                detailed_guide = get_detailed_recipe_guide(recipe)
                print(f"Detailed Guide for {recipe['title']}:\n{detailed_guide}")
                break
        else:
            print("Sorry, the recipe you selected was not found.")
    else:
        print("No recipes found.")
        save_data([])  # Ensure an empty list is saved if no recipes are found

if __name__ == "__main__":
    main()
