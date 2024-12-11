import requests
import json
import os
import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

def fetch_recipes(ingredient, api_key='1'):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ingredient}&apiKey={api_key}"
    response = requests.get(url)
    print(f"API URL: {url}")
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 200:
        recipes = response.json().get('meals', [])
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
    preferences['dietary_preference'] = st.selectbox("Enter your dietary preference:", ["Vegetarian", "Non-Vegetarian", "Vegan"])
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
    prompt = f"""Provide a detailed, step-by-step cooking guide for the following recipe:\n\nTitle: {recipe['title']}\n\nIngredients:\n[Ingredients Placeholder]\n\nInstructions: [Instructions Placeholder]\n
    The cooking guide that you give must be displayed in string format
    """

    # Debugging: Print the prompt to ensure it's correct
    print(f"Generated Prompt for LLM: {prompt}")

    # LLM Configuration
    llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-70b-8192")
    output_parser=PydanticOutputParser()
    

    try:
        # Generate the detailed guide using the updated method
        detailed_guide = llm.invoke(prompt)

        # Attempt to extract the text from the response object
        if isinstance(detailed_guide, dict):
            detailed_text = detailed_guide.get("text", "Error: Could not retrieve detailed guide.")
        else:
            detailed_text = str(detailed_guide)

        # Debugging: Print the detailed guide to ensure it's generated
        print(f"Generated Detailed Guide: {detailed_text}")

        return detailed_text
    except Exception as e:
        # Debugging: Print the error message if the LLM invocation fails
        print(f"Error in LLM invocation: {e}")
        return "Error generating detailed guide."


# Streamlit App
def main():
    st.title("Recipe Recommendation System")

    st.header("Set Your Preferences")
    preferences = load_preferences()

    st.header("Enter Ingredients")
    ingredients = st.text_input("Please enter the ingredients (comma-separated): ")

    if st.button("Get Recipes"):
        ingredient_list = ingredients.split(',')
        all_recipes = []
        for ingredient in ingredient_list:
            recipes = fetch_recipes(ingredient.strip())
            if recipes:
                all_recipes.extend(recipes)

        if all_recipes:
            tagged_recipes = tag_recipes(all_recipes)
            filtered_recipes = filter_recipes_by_preferences(tagged_recipes, preferences)
            st.subheader("Filtered Recipes")
            recipe_details = extract_recipe_details(filtered_recipes)
            save_data(recipe_details)  # Save data even if there are no filtered recipes
            save_preferences(preferences)  # Save preferences every time the code runs

            for recipe in recipe_details:
                with st.expander(f"{recipe['title']}"):
                    st.image(recipe['image'])
                    st.write(f"**Diet**: {recipe['diet']}")
                    st.write(f"**Calories**: {recipe['calories']}")
                    st.write(f"**Protein**: {recipe['protein']}")
                    st.write(f"**Carbs**: {recipe['carbs']}")
                    st.write(f"**Fat**: {recipe['fat']}")
                    if st.button(f"Get Detailed Guide for {recipe['title']}", key=recipe['id']):
                        detailed_guide = get_detailed_recipe_guide(recipe)
                        st.write(f"**Detailed Guide for {recipe['title']}**")
                        st.write(detailed_guide)
        else:
            st.write("No recipes found.")

if __name__ == "__main__":
    main()
