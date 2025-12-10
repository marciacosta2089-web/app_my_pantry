import json
from typing import Dict

from pantry_app.models import (
    BarcodeMemory,
    Category,
    CookedRecipe,
    Product,
    SavedRecipe,
    SessionLocal,
    ShoppingItem,
)
from pantry_app.utils import serialize_json


class ExportImportService:
    def __init__(self, user_id: int):
        self.db = SessionLocal()
        self.user_id = user_id

    def export_all(self) -> Dict:
        return {
            "products": [self._product_dict(p) for p in self._products()],
            "categories": [self._category_dict(c) for c in self._categories()],
            "saved_recipes": [self._saved_dict(r) for r in self._saved()],
            "cooked_recipes": [self._cooked_dict(r) for r in self._cooked()],
            "shopping_items": [self._shopping_dict(i) for i in self._shopping()],
            "barcode_memory": [self._barcode_dict(b) for b in self._barcode()],
        }

    def import_data(self, payload: Dict):
        # merge: overwrite by name where possible
        for cat in payload.get("categories", []):
            existing = (
                self.db.query(Category)
                .filter_by(name=cat.get("name"), user_id=self.user_id)
                .first()
            )
            if not existing:
                self.db.add(Category(name=cat.get("name"), user_id=self.user_id))
        self.db.commit()

        name_to_cat = {
            c.name: c.id
            for c in self.db.query(Category).filter_by(user_id=self.user_id).all()
        }

        for prod in payload.get("products", []):
            category_id = name_to_cat.get(prod.get("category"))
            existing = (
                self.db.query(Product)
                .filter_by(name=prod.get("name"), user_id=self.user_id)
                .first()
            )
            if existing:
                existing.quantity = prod.get("quantity", existing.quantity)
                existing.unit = prod.get("unit", existing.unit)
                existing.low_stock_threshold = prod.get(
                    "low_stock_threshold", existing.low_stock_threshold
                )
                existing.location = prod.get("location", existing.location)
                existing.category_id = category_id or existing.category_id
                existing.notes = prod.get("notes", existing.notes)
            else:
                self.db.add(
                    Product(
                        name=prod.get("name"),
                        quantity=prod.get("quantity", 0),
                        unit=prod.get("unit", "g"),
                        low_stock_threshold=prod.get("low_stock_threshold", 0),
                        location=prod.get("location", "pantry"),
                        category_id=category_id,
                        notes=prod.get("notes", ""),
                        user_id=self.user_id,
                    )
                )
        self.db.commit()

        for rec in payload.get("saved_recipes", []):
            if not (
                self.db.query(SavedRecipe)
                .filter_by(name=rec.get("name"), user_id=self.user_id)
                .first()
            ):
                self.db.add(
                    SavedRecipe(
                        name=rec.get("name"),
                        ingredients=serialize_json(rec.get("ingredients", [])),
                        instructions=rec.get("instructions", ""),
                        tags=serialize_json(rec.get("tags", [])),
                        servings=rec.get("servings", 1),
                        user_id=self.user_id,
                    )
                )
        self.db.commit()

        for rec in payload.get("cooked_recipes", []):
            cooked_at = rec.get("cooked_at")
            if isinstance(cooked_at, str):
                try:
                    import datetime as dt

                    cooked_at = dt.datetime.fromisoformat(cooked_at)
                except Exception:
                    cooked_at = None
            self.db.add(
                CookedRecipe(
                    name=rec.get("name"),
                    ingredients=serialize_json(rec.get("ingredients", [])),
                    instructions=rec.get("instructions", ""),
                    tags=serialize_json(rec.get("tags", [])),
                    servings=rec.get("servings", 1),
                    cooked_at=cooked_at,
                    rating=rec.get("rating"),
                    user_id=self.user_id,
                )
            )
        self.db.commit()

        for item in payload.get("shopping_items", []):
            self.db.add(
                ShoppingItem(
                    name=item.get("name"),
                    quantity=item.get("quantity", 1),
                    unit=item.get("unit", "units"),
                    status=item.get("status", "to_buy"),
                    user_id=self.user_id,
                )
            )
        self.db.commit()

        for mem in payload.get("barcode_memory", []):
            if not self.db.query(BarcodeMemory).filter_by(barcode=mem.get("barcode")).first():
                self.db.add(
                    BarcodeMemory(
                        barcode=mem.get("barcode"),
                        name=mem.get("name"),
                        category_name=mem.get("category_name"),
                        user_id=self.user_id,
                    )
                )
        self.db.commit()

    # helpers
    def _products(self):
        return self.db.query(Product).filter_by(user_id=self.user_id).all()

    def _categories(self):
        return self.db.query(Category).filter_by(user_id=self.user_id).all()

    def _saved(self):
        return self.db.query(SavedRecipe).filter_by(user_id=self.user_id).all()

    def _cooked(self):
        return self.db.query(CookedRecipe).filter_by(user_id=self.user_id).all()

    def _shopping(self):
        return self.db.query(ShoppingItem).filter_by(user_id=self.user_id).all()

    def _barcode(self):
        return self.db.query(BarcodeMemory).filter_by(user_id=self.user_id).all()

    def _product_dict(self, prod: Product):
        return {
            "name": prod.name,
            "quantity": prod.quantity,
            "unit": prod.unit,
            "low_stock_threshold": prod.low_stock_threshold,
            "location": prod.location,
            "category": prod.category.name if prod.category else None,
            "notes": prod.notes,
        }

    def _category_dict(self, cat: Category):
        return {"name": cat.name}

    def _saved_dict(self, rec: SavedRecipe):
        return {
            "name": rec.name,
            "ingredients": json.loads(rec.ingredients),
            "instructions": rec.instructions,
            "tags": json.loads(rec.tags),
            "servings": rec.servings,
        }

    def _cooked_dict(self, rec: CookedRecipe):
        return {
            "name": rec.name,
            "ingredients": json.loads(rec.ingredients),
            "instructions": rec.instructions,
            "tags": json.loads(rec.tags),
            "servings": rec.servings,
            "cooked_at": rec.cooked_at.isoformat() if rec.cooked_at else None,
            "rating": rec.rating,
        }

    def _shopping_dict(self, item: ShoppingItem):
        return {
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "status": item.status,
        }

    def _barcode_dict(self, mem: BarcodeMemory):
        return {
            "barcode": mem.barcode,
            "name": mem.name,
            "category_name": mem.category_name,
        }
