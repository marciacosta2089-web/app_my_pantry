import datetime as dt
import random
from typing import Dict, List, Tuple

from pantry_app.llm import get_recipes_from_llm
from pantry_app.models import CookedRecipe, Product, SavedRecipe, SessionLocal
from pantry_app.utils import convert_quantity, serialize_json


SPICE_CATEGORIES = {"Spices"}


class RecipeService:
    def __init__(self, user_id: int, preferred_units: str = "metric"):
        self.db = SessionLocal()
        self.user_id = user_id
        self.preferred_units = preferred_units

    def suggest_recipes(
        self,
        servings: int,
        preferences: Dict,
        keyword: str = "",
        only_have: bool = False,
        minimize_missing: bool = False,
        ignore_spices: bool = True,
    ):
        inventory_items = self.db.query(Product).filter_by(user_id=self.user_id).all()
        inventory = [
            {
                "name": item.name,
                "quantity": item.quantity,
                "unit": item.unit,
                "category": item.category.name if item.category else "Other",
            }
            for item in inventory_items
        ]
        raw_recipes = get_recipes_from_llm(inventory, servings, preferences, keyword)
        recipes_with_availability = []
        for recipe in raw_recipes:
            missing, available = self._missing_ingredients(recipe["ingredients"], ignore_spices)
            if only_have and missing:
                continue
            recipes_with_availability.append({"recipe": recipe, "missing": missing, "available": available})

        if minimize_missing:
            recipes_with_availability.sort(key=lambda r: len(r["missing"]))
        return recipes_with_availability

    def _missing_ingredients(self, ingredients: List[Dict], ignore_spices: bool):
        inventory_lookup = {}
        for item in self.db.query(Product).filter_by(user_id=self.user_id).all():
            inventory_lookup[item.name.lower()] = item
        missing = []
        available = []
        for ing in ingredients:
            name = ing.get("name", "").lower()
            category = ing.get("category", "")
            if ignore_spices and category in SPICE_CATEGORIES:
                available.append({"ingredient": ing, "product": None})
                continue
            product = inventory_lookup.get(name)
            if product and product.quantity >= ing.get("quantity", 0):
                available.append({"ingredient": ing, "product": product})
            else:
                missing.append(ing)
        return missing, available

    def save_recipe(self, recipe_data: Dict):
        saved = SavedRecipe(
            name=recipe_data["name"],
            ingredients=serialize_json(recipe_data.get("ingredients", [])),
            instructions=recipe_data.get("instructions", ""),
            tags=serialize_json(recipe_data.get("tags", [])),
            servings=recipe_data.get("servings", 1),
            user_id=self.user_id,
        )
        self.db.add(saved)
        self.db.commit()
        return saved

    def cook_recipe(self, recipe_data: Dict, servings: int):
        cooked = CookedRecipe(
            name=recipe_data["name"],
            ingredients=serialize_json(recipe_data.get("ingredients", [])),
            instructions=recipe_data.get("instructions", ""),
            tags=serialize_json(recipe_data.get("tags", [])),
            servings=servings,
            cooked_at=dt.datetime.utcnow(),
            user_id=self.user_id,
        )
        self.db.add(cooked)
        self._deduct_inventory(recipe_data.get("ingredients", []))
        self.db.commit()
        return cooked

    def _deduct_inventory(self, ingredients: List[Dict]):
        for ing in ingredients:
            category = ing.get("category", "")
            if category in SPICE_CATEGORIES:
                continue
            product = self.db.query(Product).filter_by(
                name=ing.get("name", ""), user_id=self.user_id
            ).first()
            if product:
                qty = ing.get("quantity", 0)
                ing_unit = ing.get("unit", product.unit)
                qty_in_product_unit = convert_quantity(qty, ing_unit, product.unit)
                product.quantity = max(product.quantity - qty_in_product_unit, 0)
        self.db.commit()

    def saved_recipes(self):
        return self.db.query(SavedRecipe).filter_by(user_id=self.user_id).all()

    def cooked_recipes(self):
        return (
            self.db.query(CookedRecipe)
            .filter_by(user_id=self.user_id)
            .order_by(CookedRecipe.cooked_at.desc())
            .all()
        )

    def rate_cooked(self, cooked_id: int, rating: int):
        cooked = (
            self.db.query(CookedRecipe)
            .filter_by(id=cooked_id, user_id=self.user_id)
            .first()
        )
        if not cooked:
            raise ValueError("Cooked recipe not found")
        cooked.rating = rating
        self.db.commit()
        return cooked
