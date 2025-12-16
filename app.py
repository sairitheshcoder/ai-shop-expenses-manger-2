from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Expense, User
from ai_utils import parse_expense_text, generate_insights

app = Flask(__name__)

# DB + session config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "change-this-secret-key"  # demo only

db.init_app(app)

with app.app_context():
    db.create_all()


def current_user_id():
    return session.get("user_id")


def login_required_json():
    if not current_user_id():
        return jsonify({"error": "Not logged in"}), 401


# -------- Auth routes --------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template("register.html", error="Email and password required")

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template("register.html", error="Email already registered")

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        session["email"] = user.email
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return render_template("login.html", error="Invalid email or password")

        session["user_id"] = user.id
        session["email"] = user.email
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------- Main page --------

@app.route("/")
def home():
    if not current_user_id():
        return redirect(url_for("login"))
    return render_template("index.html", email=session.get("email"))


# -------- Expense APIs (per user) --------

@app.post("/api/expense")
def add_expense():
    if not current_user_id():
        return login_required_json()

    data = request.get_json() or {}
    date_str = data.get("date")
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")

    expense = Expense(
        user_id=current_user_id(),
        date=datetime.strptime(date_str, "%Y-%m-%d").date(),
        amount=float(amount),
        category=category,
        description=description,
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({"message": "Expense added"}), 201


@app.get("/api/expense")
def list_expenses():
    if not current_user_id():
        return login_required_json()

    expenses = (
        Expense.query
        .filter_by(user_id=current_user_id())
        .order_by(Expense.date.desc())
        .all()
    )
    result = [
        {
            "id": e.id,
            "date": e.date.isoformat(),
            "amount": e.amount,
            "category": e.category,
            "description": e.description,
        }
        for e in expenses
    ]
    return jsonify(result)


# -------- AI APIs (use same user's data) --------

@app.post("/api/ai/parse-text")
def ai_parse_text():
    if not current_user_id():
        return login_required_json()

    data = request.get_json() or {}
    text = data.get("text", "")
    parsed = parse_expense_text(text)
    return jsonify(parsed)


@app.get("/api/ai/insights")
def ai_insights():
    if not current_user_id():
        return login_required_json()

    cutoff = datetime.utcnow().date() - timedelta(days=30)
    expenses = Expense.query.filter(
        Expense.user_id == current_user_id(),
        Expense.date >= cutoff
    ).all()
    lines = [
        f"{e.date.isoformat()} | {e.category} | {e.amount} | {e.description}"
        for e in expenses
    ]
    raw = "\n".join(lines)
    insights = generate_insights(raw)
    return jsonify({"insights": insights})


if __name__ == "__main__":
    app.run(debug=True)
