import datetime as dt
import json
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    default_units = Column(String, default="metric")
    theme = Column(String, default="light")
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    llm_config = Column(Text, default="{}")

    categories = relationship("Category", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="categories")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    quantity = Column(Float, default=0)
    unit = Column(String, default="g")
    low_stock_threshold = Column(Float, default=0)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")
    location = Column(String, default="pantry")
    notes = Column(Text, default="")
    barcode = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")


class SavedRecipe(Base):
    __tablename__ = "saved_recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    ingredients = Column(Text, default="[]")  # JSON list
    instructions = Column(Text, default="")
    tags = Column(Text, default="[]")  # JSON list
    servings = Column(Integer, default=1)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

    def ingredient_list(self):
        try:
            return json.loads(self.ingredients)
        except json.JSONDecodeError:
            return []

    def tag_list(self):
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            return []


class CookedRecipe(Base):
    __tablename__ = "cooked_recipes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    ingredients = Column(Text, default="[]")
    instructions = Column(Text, default="")
    tags = Column(Text, default="[]")
    servings = Column(Integer, default=1)
    cooked_at = Column(DateTime, default=dt.datetime.utcnow)
    rating = Column(Integer, default=None)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

    def ingredient_list(self):
        try:
            return json.loads(self.ingredients)
        except json.JSONDecodeError:
            return []

    def tag_list(self):
        try:
            return json.loads(self.tags)
        except json.JSONDecodeError:
            return []


class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    quantity = Column(Float, default=1)
    unit = Column(String, default="units")
    status = Column(String, default="to_buy")
    linked_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")


class BarcodeMemory(Base):
    __tablename__ = "barcode_memory"
    id = Column(Integer, primary_key=True)
    barcode = Column(String, unique=True)
    name = Column(String, nullable=False)
    category_name = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")


def init_db():
    Base.metadata.create_all(engine)


def get_default_categories():
    return [
        "Meat",
        "Fish",
        "Dairy",
        "Vegetables",
        "Fruit",
        "Grains",
        "Pasta/Rice",
        "Snacks",
        "Spices",
        "Beverages",
        "Frozen",
        "Sauces & Condiments",
        "Baking",
        "Other",
    ]


def ensure_default_user(session) -> User:
    user = session.query(User).first()
    if not user:
        from werkzeug.security import generate_password_hash

        user = User(
            username="demo",
            password_hash=generate_password_hash("demo"),
            default_units="metric",
            theme="light",
            llm_config="{}",
        )
        session.add(user)
        session.commit()
        for cat_name in get_default_categories():
            session.add(Category(name=cat_name, user_id=user.id))
        session.commit()
    return user
