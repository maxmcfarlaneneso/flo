import os
import random
import sqlite3
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DILL_DATA_DIR", BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bouquets.db"
IMAGE_DIR = BASE_DIR / "static" / "imgs"
ADMIN_KEY = os.environ.get("DILL_ADMIN_KEY", "change-me")


def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def available_images():
    extensions = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(path.name for path in IMAGE_DIR.iterdir() if path.is_file() and path.suffix.lower() in extensions)


def random_image(exclude=()):
    images = [image for image in available_images() if image not in set(exclude)]
    if not images:
        images = available_images()
    return random.choice(images) if images else ""


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS bouquets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_pence INTEGER NOT NULL CHECK(price_pence >= 0),
                image TEXT NOT NULL DEFAULT '',
                in_stock INTEGER NOT NULL DEFAULT 1,
                shopify_url TEXT NOT NULL DEFAULT '#',
                sort_order INTEGER NOT NULL DEFAULT 0
            )
        """)
        count = db.execute("SELECT COUNT(*) FROM bouquets").fetchone()[0]
        if count == 0:
            used = []
            for order, (name, price) in enumerate([
                ("Seasonal Bouquet", 3500),
                ("Florist's Choice", 4500),
                ("Gift Bouquet", 5500),
            ]):
                image = random_image(used)
                if image:
                    used.append(image)
                db.execute(
                    "INSERT INTO bouquets (name, price_pence, image, sort_order) VALUES (?, ?, ?, ?)",
                    (name, price, image, order),
                )


def require_admin():
    supplied_key = request.headers.get("X-Admin-Key", "")
    if supplied_key != ADMIN_KEY:
        abort(401)


@app.route("/")
def home():
    with get_db() as db:
        bouquets = db.execute("SELECT * FROM bouquets ORDER BY sort_order, id").fetchall()
    return render_template("index.html", bouquets=bouquets, gallery_images=available_images())


@app.get("/api/images")
def list_images():
    require_admin()
    return jsonify(available_images())


@app.post("/api/bouquets")
def add_bouquet():
    require_admin()
    data = request.get_json(force=True)
    name = str(data.get("name", "")).strip()
    if not name:
        return jsonify(error="Name is required"), 400

    try:
        price_pence = round(float(data.get("price", 0)) * 100)
    except (TypeError, ValueError):
        return jsonify(error="Price must be a number"), 400

    image = str(data.get("image", "")).strip() or random_image()
    shopify_url = str(data.get("shopify_url", "#")).strip() or "#"

    with get_db() as db:
        next_order = db.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM bouquets").fetchone()[0]
        cursor = db.execute(
            "INSERT INTO bouquets (name, price_pence, image, in_stock, shopify_url, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
            (name, price_pence, image, int(bool(data.get("in_stock", True))), shopify_url, next_order),
        )
    return jsonify(id=cursor.lastrowid), 201


@app.patch("/api/bouquets/<int:bouquet_id>")
def update_bouquet(bouquet_id):
    require_admin()
    data = request.get_json(force=True)
    allowed = {"name", "image", "shopify_url", "in_stock", "sort_order"}
    updates = {key: value for key, value in data.items() if key in allowed}

    if "price" in data:
        try:
            updates["price_pence"] = round(float(data["price"]) * 100)
        except (TypeError, ValueError):
            return jsonify(error="Price must be a number"), 400

    if "in_stock" in updates:
        updates["in_stock"] = int(bool(updates["in_stock"]))
    if not updates:
        return jsonify(error="Nothing to update"), 400

    columns = ", ".join(f"{column} = ?" for column in updates)
    with get_db() as db:
        cursor = db.execute(
            f"UPDATE bouquets SET {columns} WHERE id = ?",
            [*updates.values(), bouquet_id],
        )
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


init_db()

if __name__ == "__main__":
    app.run(debug=True)
