import os
import sqlite3
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DILL_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "site.db"
IMAGE_DIR = BASE_DIR / "static" / "imgs"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_KEY = os.environ.get("DILL_ADMIN_KEY", "change-me")
app = Flask(__name__)
app.secret_key = os.environ.get("DILL_SECRET_KEY", "change-this-secret-key")
app.permanent_session_lifetime = timedelta(minutes=10)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            price_pence INTEGER NOT NULL,
            product_type TEXT NOT NULL DEFAULT 'flower',
            image TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS content_images (
            slot TEXT PRIMARY KEY,
            image TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL UNIQUE,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            fulfilment TEXT NOT NULL,
            address TEXT,
            requested_date TEXT,
            total_pence INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            unit_price_pence INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            preferences TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        );
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT,
            event_type TEXT NOT NULL, event_date TEXT, venue TEXT,
            budget TEXT, message TEXT,
            submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS newsletter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        if connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            connection.executemany(
                "INSERT INTO products (slug,name,description,price_pence,product_type,sort_order) VALUES (?,?,?,?,?,?)",
                [
                    ("small-bouquet", "Small bouquet", "A simple seasonal bouquet for an everyday gesture.", 2500, "flower", 1),
                    ("hand-tied-bouquet", "Hand-tied bouquet", "A fuller arrangement for birthdays, thanks and celebrations.", 3500, "flower", 2),
                    ("large-bouquet", "Large bouquet", "A generous seasonal arrangement for something special.", 5000, "flower", 3),
                    ("voucher-25", "£25 gift voucher", "A Dill Flowers voucher for collection from the shop.", 2500, "voucher", 4),
                    ("voucher-50", "£50 gift voucher", "A Dill Flowers voucher for collection from the shop.", 5000, "voucher", 5),
                ],
            )
        for slot in ("hero", "wedding", "about"):
            connection.execute("INSERT OR IGNORE INTO content_images (slot,image) VALUES (?, '')", (slot,))


def image_names():
    allowed = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(p.name for p in IMAGE_DIR.iterdir() if p.is_file() and p.suffix.lower() in allowed and p.name.lower() != "logo.png")


def require_admin():
    if not session.get("admin_authenticated"):
        abort(401)
    session.permanent = True
    session.modified = True


def basket():
    return session.setdefault("basket", [])


def basket_details():
    raw = basket()
    if not raw:
        return [], 0
    ids = [int(item["product_id"]) for item in raw]
    placeholders = ",".join("?" for _ in ids)
    with db() as connection:
        products = {row["id"]: row for row in connection.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", ids)}
    items, total = [], 0
    for index, item in enumerate(raw):
        product = products.get(int(item["product_id"]))
        if not product:
            continue
        quantity = max(1, int(item.get("quantity", 1)))
        line_total = product["price_pence"] * quantity
        total += line_total
        items.append({"index": index, "product": product, "quantity": quantity, "preferences": item.get("preferences", ""), "line_total": line_total})
    return items, total


@app.context_processor
def global_context():
    return {"basket_count": sum(int(x.get("quantity", 1)) for x in session.get("basket", []))}


@app.get("/")
def home():
    with db() as connection:
        flowers = connection.execute("SELECT * FROM products WHERE active=1 AND product_type='flower' ORDER BY sort_order,id").fetchall()
        vouchers = connection.execute("SELECT * FROM products WHERE active=1 AND product_type='voucher' ORDER BY sort_order,id").fetchall()
        images = {row["slot"]: row["image"] for row in connection.execute("SELECT * FROM content_images")}
    return render_template("index.html", flowers=flowers, vouchers=vouchers, content_images=images, subscribed=request.args.get("subscribed") == "1")


@app.get("/order/<slug>")
def order_product(slug):
    with db() as connection:
        product = connection.execute("SELECT * FROM products WHERE slug=? AND active=1", (slug,)).fetchone()
    if not product:
        abort(404)
    return render_template("order_product.html", product=product)


@app.post("/basket/add/<int:product_id>")
def add_to_basket(product_id):
    with db() as connection:
        product = connection.execute("SELECT id FROM products WHERE id=? AND active=1", (product_id,)).fetchone()
    if not product:
        abort(404)
    items = basket()
    items.append({"product_id": product_id, "quantity": max(1, int(request.form.get("quantity", 1))), "preferences": request.form.get("preferences", "").strip()})
    session["basket"] = items
    session.modified = True
    return redirect(url_for("view_basket"))


@app.get("/basket")
def view_basket():
    items, total = basket_details()
    return render_template("basket.html", items=items, total=total)


@app.post("/basket/remove/<int:index>")
def remove_from_basket(index):
    items = basket()
    if 0 <= index < len(items):
        items.pop(index)
        session["basket"] = items
        session.modified = True
    return redirect(url_for("view_basket"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = basket_details()
    if not items:
        return redirect(url_for("view_basket"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        fulfilment = request.form.get("fulfilment", "Collection")
        if not name or not email or not phone:
            return render_template("checkout.html", items=items, total=total, error="Please complete your name, email and phone.", form=request.form), 400
        order_number = f"DF-{uuid4().hex[:8].upper()}"
        with db() as connection:
            cursor = connection.execute(
                "INSERT INTO orders (order_number,customer_name,email,phone,fulfilment,address,requested_date,total_pence) VALUES (?,?,?,?,?,?,?,?)",
                (order_number, name, email, phone, fulfilment, request.form.get("address", "").strip(), request.form.get("requested_date", ""), total),
            )
            order_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO order_items (order_id,product_id,product_name,unit_price_pence,quantity,preferences) VALUES (?,?,?,?,?,?)",
                [(order_id, x["product"]["id"], x["product"]["name"], x["product"]["price_pence"], x["quantity"], x["preferences"]) for x in items],
            )
        session["basket"] = []
        return redirect(url_for("order_complete", order_number=order_number))
    return render_template("checkout.html", items=items, total=total, form={})


@app.get("/order-complete/<order_number>")
def order_complete(order_number):
    return render_template("order_complete.html", order_number=order_number)


@app.post("/newsletter")
def newsletter():
    email = request.form.get("email", "").strip().lower()
    if email:
        with db() as connection:
            connection.execute("INSERT OR IGNORE INTO newsletter (email) VALUES (?)", (email,))
    return redirect(url_for("home", subscribed=1) + "#newsletter")


@app.route("/weddings-events", methods=["GET", "POST"])
def weddings_events():
    if request.method == "POST":
        form = request.form
        name, email, event_type = form.get("name", "").strip(), form.get("email", "").strip(), form.get("event_type", "").strip()
        if not name or not email or not event_type:
            return render_template("weddings_events.html", form=form, error="Please complete your name, email and event type."), 400
        with db() as connection:
            connection.execute("INSERT INTO consultations (name,email,phone,event_type,event_date,venue,budget,message) VALUES (?,?,?,?,?,?,?,?)", (name,email,form.get("phone",""),event_type,form.get("event_date",""),form.get("venue",""),form.get("budget",""),form.get("message","")))
        return redirect(url_for("consultation_sent"))
    with db() as connection:
        image = connection.execute("SELECT image FROM content_images WHERE slot='wedding'").fetchone()["image"]
    return render_template("weddings_events.html", form={}, wedding_image=image)


@app.get("/consultation-sent")
def consultation_sent():
    return render_template("consultation_sent.html")


@app.post("/api/admin/login")
def admin_login():
    if (request.get_json(silent=True) or {}).get("key") != ADMIN_KEY:
        session.clear()
        return jsonify(error="Incorrect admin key"), 401
    session.clear(); session["admin_authenticated"] = True; session.permanent = True
    return jsonify(ok=True)


@app.post("/api/admin/logout")
def admin_logout():
    session.clear(); return jsonify(ok=True)


@app.get("/api/admin/status")
def admin_status():
    return jsonify(authenticated=bool(session.get("admin_authenticated")))


@app.post("/api/images/upload")
def upload_image():
    require_admin()
    upload = request.files.get("image")
    if not upload or not upload.filename:
        return jsonify(error="Choose an image"), 400
    filename = secure_filename(upload.filename)
    suffix = Path(filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return jsonify(error="Use PNG, JPG or WebP"), 400
    stem, candidate, number = Path(filename).stem or "image", filename, 2
    while (IMAGE_DIR / candidate).exists():
        candidate = f"{stem}-{number}{suffix}"; number += 1
    upload.save(IMAGE_DIR / candidate)
    return jsonify(filename=candidate)


@app.patch("/api/content-image/<slot>")
def update_content_image(slot):
    require_admin()
    if slot not in {"hero", "wedding", "about"}:
        abort(404)
    filename = (request.get_json(silent=True) or {}).get("image", "")
    with db() as connection:
        connection.execute("UPDATE content_images SET image=? WHERE slot=?", (filename, slot))
    return jsonify(ok=True)


@app.patch("/api/products/<int:product_id>")
def update_product(product_id):
    require_admin()
    data = request.get_json(silent=True) or {}
    updates = {}
    for field in ("name", "description", "image"):
        if field in data: updates[field] = str(data[field]).strip()
    if "price" in data: updates["price_pence"] = round(float(data["price"]) * 100)
    if "active" in data: updates["active"] = 1 if data["active"] else 0
    if not updates: return jsonify(error="Nothing to update"), 400
    with db() as connection:
        sql = ",".join(f"{key}=?" for key in updates)
        connection.execute(f"UPDATE products SET {sql} WHERE id=?", [*updates.values(), product_id])
    return jsonify(ok=True)


@app.get("/health")
def health():
    return {"ok": True}


init_db()
if __name__ == "__main__": app.run(debug=True)
