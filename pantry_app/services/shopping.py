from typing import List

from pantry_app.models import Product, SessionLocal, ShoppingItem


class ShoppingService:
    def __init__(self, user_id: int):
        self.db = SessionLocal()
        self.user_id = user_id

    def auto_low_stock_items(self) -> List[ShoppingItem]:
        items = []
        low_stock = (
            self.db.query(Product)
            .filter(
                Product.user_id == self.user_id,
                Product.quantity <= Product.low_stock_threshold,
            )
            .all()
        )
        for prod in low_stock:
            existing = (
                self.db.query(ShoppingItem)
                .filter_by(user_id=self.user_id, linked_product_id=prod.id)
                .first()
            )
            if not existing:
                item = ShoppingItem(
                    name=prod.name,
                    quantity=prod.low_stock_threshold - prod.quantity + 1,
                    unit=prod.unit,
                    status="to_buy",
                    linked_product_id=prod.id,
                    user_id=self.user_id,
                )
                self.db.add(item)
        self.db.commit()
        return (
            self.db.query(ShoppingItem)
            .filter_by(user_id=self.user_id)
            .order_by(ShoppingItem.status)
            .all()
        )

    def add_item(self, name: str, quantity: float, unit: str):
        item = ShoppingItem(
            name=name,
            quantity=quantity,
            unit=unit,
            user_id=self.user_id,
            status="to_buy",
        )
        self.db.add(item)
        self.db.commit()
        return item

    def update_status(self, item_id: int, status: str, update_inventory: bool = False):
        item = (
            self.db.query(ShoppingItem)
            .filter_by(id=item_id, user_id=self.user_id)
            .first()
        )
        if not item:
            return
        item.status = status
        if status == "bought" and update_inventory:
            if item.linked_product_id:
                prod = self.db.query(Product).get(item.linked_product_id)
                if prod:
                    prod.quantity += item.quantity
            else:
                prod = Product(
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    low_stock_threshold=1,
                    location="pantry",
                    user_id=self.user_id,
                )
                self.db.add(prod)
        self.db.commit()

    def delete_item(self, item_id: int):
        item = (
            self.db.query(ShoppingItem)
            .filter_by(id=item_id, user_id=self.user_id)
            .first()
        )
        if item:
            self.db.delete(item)
            self.db.commit()

    def all_items(self) -> List[ShoppingItem]:
        return self.db.query(ShoppingItem).filter_by(user_id=self.user_id).all()
