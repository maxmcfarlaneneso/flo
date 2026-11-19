import os
import sqlite3
from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DILL_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "consultations.db"

app = Flask(__name__)


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                event_type TEXT NOT NULL,
                event_date TEXT,
                venue TEXT,
                budget TEXT,
                message TEXT,
                submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


@app.get("/")
def home():
    return render_template("index.html")


@app.route("/weddings-events", methods=["GET", "POST"])
def weddings_events():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        event_type = request.form.get("event_type", "").strip()

        if not name or not email or not event_type:
            return render_template(
                "weddings_events.html",
                error="Please complete your name, email and event type.",
                form=request.form,
            ), 400

        with sqlite3.connect(DB_PATH) as db:
            db.execute(
                """
                INSERT INTO consultations
                    (name, email, phone, event_type, event_date, venue, budget, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    request.form.get("phone", "").strip(),
                    event_type,
                    request.form.get("event_date", "").strip(),
                    request.form.get("venue", "").strip(),
                    request.form.get("budget", "").strip(),
                    request.form.get("message", "").strip(),
                ),
            )
        return redirect(url_for("consultation_sent"))

    return render_template("weddings_events.html", form={})


@app.get("/consultation-sent")
def consultation_sent():
    return render_template("consultation_sent.html")


@app.get("/health")
def health():
    return {"ok": True}


init_db()

if __name__ == "__main__":
    app.run(debug=True)
