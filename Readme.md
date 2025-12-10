# App My Pantry

A local-first pantry companion built with Flask. The app keeps your pantry, fridge, and freezer organized, suggests recipes with an LLM-friendly hook, tracks cooking history, and builds shopping lists from low-stock items. The UI is responsive for desktop and mobile.

## Features
- **Inventory** for pantry, fridge, and freezer with low-stock alerts, barcode memory, category filters, and per-item notes.
- **Recipes** generated through a placeholder `get_recipes_from_llm` integration point with advanced filters (servings, tag filters, use-only-what-I-have, minimize missing, ignore spices, high-protein/low-carb toggles).
- **Cooking flow** deducts ingredients (except spices), tracks servings and ratings, and stores cooking history.
- **Saved recipes & history** with rating controls and quick cook actions.
- **Shopping list** auto-populates low-stock items and supports custom items with optional inventory updates when bought.
- **Settings** for metric/imperial units, light/dark theme, category management, and JSON export/import for backup and migration.
- **Authentication** ready for multiple users with a demo account (`demo`/`demo`) created on first launch.

## Installation
1. Ensure Python 3.10+ is available.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the app
```bash
python -m pantry_app.app
```
The server starts on `http://localhost:5000`. Log in with the default credentials `demo` / `demo`.

## Project structure
- `pantry_app/app.py` – Flask entrypoint and routes.
- `pantry_app/models.py` – SQLAlchemy models and database initialization.
- `pantry_app/services/` – business logic for inventory, recipes, shopping, export/import, authentication, and settings.
- `pantry_app/llm.py` – placeholder LLM integration that you can replace with a real API call.
- `pantry_app/templates/` – Bootstrap-based responsive UI.
- `pantry_app/static/` – CSS/JS assets.

## Data storage
SQLite is stored at `app.db` in the project root. Data persists across sessions. Barcode scans are cached locally to autofill known items.

## LLM integration
Replace `get_recipes_from_llm` in `pantry_app/llm.py` with your real model call. The function receives:
```python
get_recipes_from_llm(inventory: List[Dict], servings: int, preferences: Dict, keyword: str = "") -> List[Dict]
```
It should return recipe dicts with `name`, `ingredients`, `instructions`, `tags`, and `servings`.

## Units and conversions
The app defaults to metric units. Switching to imperial in Settings will present imperial unit options; conversions inside cooking deduction use a simple conversion table in `pantry_app/utils.py`.

## Export / Import
Use the Settings page to export all data as JSON. Importing merges categories and products and appends history and saved items. Always review backups before importing into another machine.

## Notes for mobile
The UI uses Bootstrap 5 for responsive layouts, collapsible navigation, and touch-friendly controls.

## Security
Passwords are hashed with Werkzeug utilities. For a local setup, this is sufficient; integrate a stronger auth provider if you extend the app for remote access.
