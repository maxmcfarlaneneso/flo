import os
import random
import sqlite3
from pathlib import Path

from datetime import timedelta

from flask import Flask, abort, jsonify, render_template, request, session
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DILL_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bouquets.db"
IMAGE_DIR = BASE_DIR / "static" / "imgs"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_KEY = os.environ.get("DILL_ADMIN_KEY", "change-me")

app = Flask(__name__)
app.secret_key = os.environ.get("DILL_SECRET_KEY", "change-this-secret-key")
app.permanent_session_lifetime = timedelta(minutes=10)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def available_images():
    extensions = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(
        path.name
        for path in IMAGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in extensions and path.name.lower() != "logo.png"
    )


def random_image(exclude=()):
    excluded = set(exclude)
    images = [image for image in available_images() if image not in excluded]
    if not images:
        images = available_images()
    return random.choice(images) if images else ""


def init_db():
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS bouquets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_pence INTEGER NOT NULL CHECK(price_pence >= 0),
                image TEXT NOT NULL DEFAULT '',
                in_stock INTEGER NOT NULL DEFAULT 1,
                shopify_url TEXT NOT NULL DEFAULT '#',
                category TEXT NOT NULL DEFAULT 'Other',
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        columns = {row[1] for row in db.execute("PRAGMA table_info(bouquets)").fetchall()}
        if "category" not in columns:
            db.execute("ALTER TABLE bouquets ADD COLUMN category TEXT NOT NULL DEFAULT 'Other'")


def require_admin():
    if not session.get("admin_authenticated"):
        abort(401)
    # Refresh the 10-minute session whenever the owner performs an authenticated action.
    session.permanent = True
    session.modified = True


@app.get("/")
def home():
    with get_db() as db:
        bouquets = db.execute("SELECT * FROM bouquets ORDER BY category, sort_order, id").fetchall()

    preferred_order = ["Christmas", "Weddings", "Funerals", "Birthdays", "Other"]
    grouped = {}
    for bouquet in bouquets:
        category = bouquet["category"] or "Other"
        grouped.setdefault(category, []).append(bouquet)

    ordered_categories = [category for category in preferred_order if category in grouped]
    ordered_categories.extend(sorted(category for category in grouped if category not in preferred_order))
    bouquet_groups = [(category, grouped[category]) for category in ordered_categories]

    return render_template(
        "index.html",
        bouquets=bouquets,
        bouquet_groups=bouquet_groups,
        gallery_images=available_images(),
    )


@app.post("/api/admin/login")
def admin_login():
    data = request.get_json(silent=True) or {}
    if str(data.get("key", "")) != ADMIN_KEY:
        session.clear()
        return jsonify(error="Incorrect admin key"), 401
    session.clear()
    session["admin_authenticated"] = True
    session.permanent = True
    return jsonify(ok=True, expires_in=600)


@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return jsonify(ok=True)


@app.get("/api/admin/status")
def admin_status():
    return jsonify(authenticated=bool(session.get("admin_authenticated")), expires_in=600)


@app.get("/api/images")
def list_images():
    require_admin()
    return jsonify(available_images())


@app.post("/api/images/upload")
def upload_image():
    require_admin()
    uploaded = request.files.get("image")
    if not uploaded or not uploaded.filename:
        return jsonify(error="Choose an image to upload"), 400

    filename = secure_filename(uploaded.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify(error="Use a PNG, JPG, JPEG or WebP image"), 400

    stem = Path(filename).stem or "bouquet"
    candidate = f"{stem}{suffix}"
    counter = 2
    while (IMAGE_DIR / candidate).exists():
        candidate = f"{stem}-{counter}{suffix}"
        counter += 1

    uploaded.save(IMAGE_DIR / candidate)
    return jsonify(filename=candidate), 201




@app.post("/api/bouquets")
def add_bouquet():
    require_admin()
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify(error="Name is required"), 400

    try:
        price_pence = round(float(data.get("price", 0)) * 100)
    except (TypeError, ValueError):
        return jsonify(error="Price must be a number"), 400
    if price_pence < 0:
        return jsonify(error="Price cannot be negative"), 400

    image = str(data.get("image", "")).strip()
    if image and image not in available_images():
        return jsonify(error="Selected image was not found"), 400
    image = image or random_image()

    shopify_url = str(data.get("shopify_url", "")).strip()
    category = str(data.get("category", "Other")).strip() or "Other"
    in_stock = 1 if data.get("in_stock", True) else 0

    with get_db() as db:
        next_order = db.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM bouquets").fetchone()[0]
        cursor = db.execute(
            "INSERT INTO bouquets (name, price_pence, image, in_stock, shopify_url, category, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, price_pence, image, in_stock, shopify_url, category, next_order),
        )
        bouquet_id = cursor.lastrowid
    return jsonify(id=bouquet_id), 201


@app.patch("/api/bouquets/<int:bouquet_id>")
def update_bouquet(bouquet_id):
    require_admin()
    data = request.get_json(silent=True) or {}
    updates = {}

    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify(error="Name is required"), 400
        updates["name"] = name
    if "price" in data:
        try:
            updates["price_pence"] = round(float(data["price"]) * 100)
        except (TypeError, ValueError):
            return jsonify(error="Price must be a number"), 400
    if "image" in data:
        image = str(data["image"]).strip()
        if image and image not in available_images():
            return jsonify(error="Selected image was not found"), 400
        updates["image"] = image
    if "shopify_url" in data:
        updates["shopify_url"] = str(data["shopify_url"]).strip()
    if "category" in data:
        updates["category"] = str(data["category"]).strip() or "Other"
    if "in_stock" in data:
        updates["in_stock"] = 1 if data["in_stock"] else 0
    if "sort_order" in data:
        updates["sort_order"] = int(data["sort_order"])

    if not updates:
        return jsonify(error="Nothing to update"), 400

    sql = ", ".join(f"{column} = ?" for column in updates)
    with get_db() as db:
        cursor = db.execute(f"UPDATE bouquets SET {sql} WHERE id = ?", [*updates.values(), bouquet_id])
        if cursor.rowcount == 0:
            abort(404)
    return jsonify(ok=True)


@app.delete("/api/bouquets/<int:bouquet_id>")
def delete_bouquet(bouquet_id):
    require_admin()
    with get_db() as db:
        cursor = db.execute("DELETE FROM bouquets WHERE id = ?", (bouquet_id,))
        if cursor.rowcount == 0:
            abort(404)
    return "", 204


@app.get("/health")
def health():
    return jsonify(ok=True)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
