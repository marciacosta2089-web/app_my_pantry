import json

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from pantry_app.models import SavedRecipe, SessionLocal, User, ensure_default_user, init_db
from pantry_app.services.auth import AuthService
from pantry_app.services.export_import import ExportImportService
from pantry_app.services.inventory import InventoryService
from pantry_app.services.recipes import RecipeService
from pantry_app.services.settings import SettingsService
from pantry_app.services.shopping import ShoppingService
from pantry_app.utils import METRIC_UNITS, IMPERIAL_UNITS

init_db()

app = Flask(__name__)
app.secret_key = "app-my-pantry-secret"


def current_user() -> User:
    db = SessionLocal()
    ensure_default_user(db)
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.query(User).get(user_id)


def login_required(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
@login_required
def home():
    return redirect(url_for("inventory"))


@app.route("/login", methods=["GET", "POST"])
def login():
    auth = AuthService()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = auth.verify(username, password)
        if user:
            session["user_id"] = user.id
            flash("Welcome back!", "success")
            return redirect(url_for("inventory"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for("login"))


@app.route("/inventory")
@login_required
def inventory():
    user = current_user()
    inv = InventoryService(user.id)
    cat_id = request.args.get("category_id")
    location = request.args.get("location")
    low_stock = request.args.get("low_stock")
    category_filter = int(cat_id) if cat_id else None
    products = inv.get_products(location=location, category_id=category_filter)
    if low_stock:
        products = [p for p in products if p.quantity <= p.low_stock_threshold]
    return render_template(
        "inventory.html",
        products=products,
        categories=inv.categories(),
        units=METRIC_UNITS if user.default_units == "metric" else IMPERIAL_UNITS,
        user=user,
    )


@app.route("/barcode/<barcode>")
@login_required
def barcode_lookup(barcode):
    user = current_user()
    inv = InventoryService(user.id)
    memory = inv.barcode_lookup(barcode)
    if not memory:
        return jsonify({"found": False})
    return jsonify({"found": True, "name": memory.name, "category_name": memory.category_name})


@app.route("/inventory/add", methods=["POST"])
@login_required
def add_product():
    user = current_user()
    inv = InventoryService(user.id)
    barcode = request.form.get("barcode")
    category_id = request.form.get("category_id")
    category_id = int(category_id) if category_id else None
    inv.add_product(
        name=request.form.get("name"),
        quantity=float(request.form.get("quantity", 0)),
        unit=request.form.get("unit"),
        low_stock_threshold=float(request.form.get("low_stock_threshold", 0)),
        category_id=category_id,
        location=request.form.get("location"),
        notes=request.form.get("notes", ""),
        barcode=barcode,
    )
    flash("Product added", "success")
    return redirect(url_for("inventory"))


@app.route("/inventory/<int:product_id>/edit", methods=["POST"])
@login_required
def edit_product(product_id):
    user = current_user()
    inv = InventoryService(user.id)
    category_id = request.form.get("category_id")
    category_id = int(category_id) if category_id else None
    inv.update_product(
        product_id,
        name=request.form.get("name"),
        quantity=float(request.form.get("quantity", 0)),
        unit=request.form.get("unit"),
        low_stock_threshold=float(request.form.get("low_stock_threshold", 0)),
        category_id=category_id,
        location=request.form.get("location"),
        notes=request.form.get("notes", ""),
        barcode=request.form.get("barcode"),
    )
    flash("Product updated", "success")
    return redirect(url_for("inventory"))


@app.route("/inventory/<int:product_id>/delete")
@login_required
def delete_product(product_id):
    user = current_user()
    inv = InventoryService(user.id)
    inv.delete_product(product_id)
    flash("Product deleted", "info")
    return redirect(url_for("inventory"))


@app.route("/recipes", methods=["GET", "POST"])
@login_required
def recipes():
    user = current_user()
    service = RecipeService(user.id, preferred_units=user.default_units)
    results = []
    keyword = request.form.get("keyword", "") if request.method == "POST" else ""
    servings = int(request.form.get("servings", 1)) if request.method == "POST" else 1
    preferences = {
        "high_protein": bool(request.form.get("high_protein")),
        "low_carb": bool(request.form.get("low_carb")),
        "tags": request.form.getlist("tags"),
    }
    options = {
        "only_have": bool(request.form.get("only_have")),
        "minimize_missing": bool(request.form.get("minimize_missing")),
        "ignore_spices": bool(request.form.get("ignore_spices", True)),
    }
    if request.method == "POST":
        suggestions = service.suggest_recipes(
            servings=servings,
            preferences=preferences,
            keyword=keyword,
            only_have=options["only_have"],
            minimize_missing=options["minimize_missing"],
            ignore_spices=options["ignore_spices"],
        )
        results = suggestions[:6]
    return render_template(
        "recipes.html",
        results=results,
        saved=service.saved_recipes(),
        cooked=service.cooked_recipes(),
        servings=servings,
        keyword=keyword,
        preferences=preferences,
        options=options,
        units=METRIC_UNITS if user.default_units == "metric" else IMPERIAL_UNITS,
        user=user,
    )


@app.route("/recipes/save", methods=["POST"])
@login_required
def save_recipe():
    user = current_user()
    service = RecipeService(user.id)
    recipe_data = json.loads(request.form.get("recipe"))
    service.save_recipe(recipe_data)
    flash("Recipe saved", "success")
    return redirect(url_for("recipes"))


@app.route("/recipes/cook", methods=["POST"])
@login_required
def cook_recipe():
    user = current_user()
    service = RecipeService(user.id)
    recipe_data = json.loads(request.form.get("recipe"))
    servings = int(request.form.get("servings", recipe_data.get("servings", 1)))
    service.cook_recipe(recipe_data, servings)
    flash("Recipe cooked and inventory updated", "success")
    return redirect(url_for("history"))


@app.route("/recipes/<int:recipe_id>/rate", methods=["POST"])
@login_required
def rate_recipe(recipe_id):
    user = current_user()
    service = RecipeService(user.id)
    rating = int(request.form.get("rating", 0))
    service.rate_cooked(recipe_id, rating)
    flash("Rating saved", "success")
    return redirect(url_for("history"))


@app.route("/recipes/<int:recipe_id>/cook_saved")
@login_required
def cook_saved(recipe_id):
    user = current_user()
    db = SessionLocal()
    recipe_entry = db.query(SavedRecipe).filter_by(id=recipe_id, user_id=user.id).first()
    if not recipe_entry:
        flash("Saved recipe not found", "warning")
        return redirect(url_for("recipes"))
    service = RecipeService(user.id)
    data = {
        "name": recipe_entry.name,
        "ingredients": json.loads(recipe_entry.ingredients),
        "instructions": recipe_entry.instructions,
        "tags": json.loads(recipe_entry.tags),
        "servings": recipe_entry.servings,
    }
    service.cook_recipe(data, recipe_entry.servings)
    flash("Saved recipe cooked", "success")
    return redirect(url_for("history"))


@app.route("/history")
@login_required
def history():
    user = current_user()
    service = RecipeService(user.id)
    cooked = service.cooked_recipes()
    return render_template("history.html", cooked=cooked, user=user)


@app.route("/shopping", methods=["GET", "POST"])
@login_required
def shopping():
    user = current_user()
    service = ShoppingService(user.id)
    if request.method == "POST":
        service.add_item(
            request.form.get("name"),
            float(request.form.get("quantity", 1)),
            request.form.get("unit"),
        )
        flash("Item added", "success")
        return redirect(url_for("shopping"))
    items = service.auto_low_stock_items()
    return render_template(
        "shopping.html",
        items=items,
        units=METRIC_UNITS if user.default_units == "metric" else IMPERIAL_UNITS,
        user=user,
    )


@app.route("/shopping/<int:item_id>/status", methods=["POST"])
@login_required
def shopping_status(item_id):
    user = current_user()
    service = ShoppingService(user.id)
    status = request.form.get("status")
    update_inventory = bool(request.form.get("update_inventory"))
    service.update_status(item_id, status, update_inventory)
    flash("Shopping item updated", "success")
    return redirect(url_for("shopping"))


@app.route("/shopping/<int:item_id>/delete")
@login_required
def shopping_delete(item_id):
    user = current_user()
    service = ShoppingService(user.id)
    service.delete_item(item_id)
    flash("Item removed", "info")
    return redirect(url_for("shopping"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = current_user()
    inv = InventoryService(user.id)
    settings_service = SettingsService(user.id)
    if request.method == "POST":
        units = request.form.get("units")
        theme = request.form.get("theme")
        settings_service.update(default_units=units, theme=theme)
        flash("Settings updated", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", user=user, categories=inv.categories())


@app.route("/settings/category", methods=["POST"])
@login_required
def manage_category():
    user = current_user()
    inv = InventoryService(user.id)
    action = request.form.get("action")
    if action == "create":
        inv.add_category(request.form.get("name"))
    elif action == "rename":
        inv.update_category(int(request.form.get("category_id")), request.form.get("name"))
    elif action == "delete":
        inv.delete_category(int(request.form.get("category_id")))
    flash("Categories updated", "success")
    return redirect(url_for("settings"))


@app.route("/export")
@login_required
def export_data():
    user = current_user()
    service = ExportImportService(user.id)
    data = service.export_all()
    return jsonify(data)


@app.route("/import", methods=["POST"])
@login_required
def import_data():
    user = current_user()
    service = ExportImportService(user.id)
    file = request.files.get("file")
    if file:
        payload = json.load(file.stream)
        service.import_data(payload)
        flash("Data imported", "success")
    return redirect(url_for("settings"))


@app.context_processor
def inject_globals():
    user = current_user()
    theme = user.theme if user else "light"
    return {"current_theme": theme}


def create_app():
    return app


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
