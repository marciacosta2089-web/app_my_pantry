from typing import List, Optional

from pantry_app.models import BarcodeMemory, Category, Product, SessionLocal


class InventoryService:
    def __init__(self, user_id: int):
        self.db = SessionLocal()
        self.user_id = user_id

    def categories(self) -> List[Category]:
        return (
            self.db.query(Category)
            .filter((Category.user_id == self.user_id) | (Category.user_id.is_(None)))
            .order_by(Category.name)
            .all()
        )

    def add_product(
        self,
        name: str,
        quantity: float,
        unit: str,
        low_stock_threshold: float,
        category_id: Optional[int],
        location: str,
        notes: str = "",
        barcode: Optional[str] = None,
    ) -> Product:
        product = Product(
            name=name,
            quantity=quantity,
            unit=unit,
            low_stock_threshold=low_stock_threshold,
            category_id=category_id,
            location=location,
            notes=notes,
            barcode=barcode,
            user_id=self.user_id,
        )
        self.db.add(product)
        self.db.commit()
        if barcode:
            existing = self.db.query(BarcodeMemory).filter_by(barcode=barcode).first()
            if not existing:
                category_name = None
                if category_id:
                    category = self.db.query(Category).get(category_id)
                    category_name = category.name if category else None
                self.db.add(
                    BarcodeMemory(
                        barcode=barcode,
                        name=name,
                        category_name=category_name,
                        user_id=self.user_id,
                    )
                )
                self.db.commit()
        return product

    def update_product(self, product_id: int, **kwargs) -> Product:
        product = self.db.query(Product).filter_by(id=product_id, user_id=self.user_id).first()
        if not product:
            raise ValueError("Product not found")
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        self.db.commit()
        return product

    def delete_product(self, product_id: int):
        product = self.db.query(Product).filter_by(id=product_id, user_id=self.user_id).first()
        if product:
            self.db.delete(product)
            self.db.commit()

    def low_stock_products(self) -> List[Product]:
        return (
            self.db.query(Product)
            .filter(
                Product.user_id == self.user_id,
                Product.quantity <= Product.low_stock_threshold,
            )
            .all()
        )

    def get_products(self, location: Optional[str] = None, category_id: Optional[int] = None):
        query = self.db.query(Product).filter(Product.user_id == self.user_id)
        if location:
            query = query.filter(Product.location == location)
        if category_id:
            query = query.filter(Product.category_id == category_id)
        return query.all()

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter_by(id=product_id, user_id=self.user_id).first()

    def barcode_lookup(self, barcode: str) -> Optional[BarcodeMemory]:
        return self.db.query(BarcodeMemory).filter_by(barcode=barcode).first()

    def add_category(self, name: str) -> Category:
        cat = Category(name=name, user_id=self.user_id)
        self.db.add(cat)
        self.db.commit()
        return cat

    def update_category(self, category_id: int, name: str):
        cat = self.db.query(Category).filter_by(id=category_id, user_id=self.user_id).first()
        if not cat:
            raise ValueError("Category not found")
        cat.name = name
        self.db.commit()

    def delete_category(self, category_id: int, fallback_category_name: str = "Other"):
        cat = self.db.query(Category).filter_by(id=category_id, user_id=self.user_id).first()
        if not cat:
            return
        fallback = (
            self.db.query(Category)
            .filter_by(name=fallback_category_name, user_id=self.user_id)
            .first()
        )
        if not fallback:
            fallback = Category(name=fallback_category_name, user_id=self.user_id)
            self.db.add(fallback)
            self.db.commit()
        for product in self.db.query(Product).filter_by(category_id=cat.id).all():
            product.category_id = fallback.id
        self.db.delete(cat)
        self.db.commit()
