import json
from functools import wraps
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, session, url_for
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "student_performance.csv"
USER_FILE = BASE_DIR / "users.json"

app = Flask(__name__)
app.secret_key = "a4f9d243-5c3e-4b51-95c8-aed12b6de7f1"

FEATURE_COLUMNS = [
    "StudyHours",
    "Attendance",
    "AssignmentsScore",
    "Participation",
    "PreviousGrade",
]


def load_users():
    if USER_FILE.exists():
        try:
            return json.loads(USER_FILE.read_text())
        except json.JSONDecodeError:
            pass

    users = {
        "teacher": {
            "password": generate_password_hash("password123"),
            "role": "teacher",
        },
        "student": {
            "password": generate_password_hash("student123"),
            "role": "student",
        },
    }
    USER_FILE.write_text(json.dumps(users, indent=2))
    return users


def save_users(users):
    USER_FILE.write_text(json.dumps(users, indent=2))


def load_dataset():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset file not found: {DATA_FILE}")

    return pd.read_csv(DATA_FILE)


def train_model(data):
    X = data[FEATURE_COLUMNS]
    y = data["Marks"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    return {
        "model": model,
        "mae": round(mean_absolute_error(y_test, predictions), 2),
        "r2": round(r2_score(y_test, predictions), 2),
        "row_count": len(data),
        "preview": data.head(8).to_dict(orient="records"),
        "columns": data.columns.tolist(),
    }


users = load_users()
app_data = train_model(load_dataset())


def auth_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        user = users.get(username)
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            session["role"] = user["role"]
            flash("Successfully signed in.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if not username or not password or password != confirm_password:
            flash("Please provide a valid username and matching passwords.", "danger")
            return render_template("register.html")

        if username in users:
            flash("Username already exists. Choose another one.", "danger")
            return render_template("register.html")

        users[username] = {
            "password": generate_password_hash(password),
            "role": role,
        }
        save_users(users)

        session["username"] = username
        session["role"] = role
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@auth_required
def dashboard():
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        row_count=app_data["row_count"],
        mae=app_data["mae"],
        r2=app_data["r2"],
        preview=app_data["preview"],
        columns=app_data["columns"],
    )


@app.route("/predict", methods=["GET", "POST"])
@auth_required
def predict():
    if request.method == "POST":
        try:
            inputs = {
                "study_hours": float(request.form["study_hours"]),
                "attendance": float(request.form["attendance"]),
                "assignments_score": float(request.form["assignments_score"]),
                "participation": float(request.form["participation"]),
                "previous_grade": float(request.form["previous_grade"]),
            }
            values = [
                inputs["study_hours"],
                inputs["attendance"],
                inputs["assignments_score"],
                inputs["participation"],
                inputs["previous_grade"],
            ]
            prediction = app_data["model"].predict([values])[0]
            predicted_value = round(float(prediction), 1)

            return render_template(
                "results.html",
                predicted=predicted_value,
                inputs=inputs,
            )
        except ValueError:
            flash("Please enter valid numeric values.", "danger")

    return render_template("predict.html")


if __name__ == "__main__":
    app.run(debug=True)
