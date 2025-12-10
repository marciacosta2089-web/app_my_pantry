import random
from typing import Dict, List

SAMPLE_INGREDIENTS = [
    {"name": "chicken breast", "unit": "g", "category": "Meat"},
    {"name": "tomato", "unit": "g", "category": "Vegetables"},
    {"name": "onion", "unit": "g", "category": "Vegetables"},
    {"name": "garlic", "unit": "g", "category": "Spices"},
    {"name": "olive oil", "unit": "ml", "category": "Sauces & Condiments"},
    {"name": "rice", "unit": "g", "category": "Pasta/Rice"},
    {"name": "pasta", "unit": "g", "category": "Pasta/Rice"},
    {"name": "spinach", "unit": "g", "category": "Vegetables"},
    {"name": "cheese", "unit": "g", "category": "Dairy"},
]

SAMPLE_TAGS = [
    "gluten-free",
    "dairy-free",
    "vegan",
    "vegetarian",
    "spicy",
    "quick-meal",
    "budget",
    "high-protein",
    "low-carb",
    "kid-friendly",
]


# Placeholder LLM integration point
# Replace get_recipes_from_llm implementation with a real API call if available.
def get_recipes_from_llm(inventory: List[Dict], servings: int, preferences: Dict, keyword: str = ""):
    recipes = []
    for i in range(8):
        ing_count = random.randint(4, 7)
        ingredients = []
        for _ in range(ing_count):
            ing = random.choice(SAMPLE_INGREDIENTS)
            ingredients.append(
                {
                    "name": ing["name"],
                    "quantity": random.randint(50, 300),
                    "unit": ing["unit"],
                    "category": ing["category"],
                }
            )
        tags = random.sample(SAMPLE_TAGS, k=random.randint(2, 4))
        name = f"{keyword.title() + ' ' if keyword else ''}Recipe {i + 1}"
        recipes.append(
            {
                "name": name,
                "ingredients": ingredients,
                "instructions": "Combine ingredients and cook until delicious. Adjust seasoning to taste.",
                "tags": tags,
                "servings": servings,
            }
        )
    return recipes
