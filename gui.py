import json
import tkinter as tk
import tkinter.messagebox as messagebox
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "student_performance.csv"
USER_FILE = BASE_DIR / "users.json"
FEATURE_COLUMNS = [
    "StudyHours",
    "Attendance",
    "AssignmentsScore",
    "Participation",
    "PreviousGrade",
]
DEFAULT_USERS = {
    "teacher": {
        "password": generate_password_hash("password123"),
        "role": "teacher",
    },
    "student": {
        "password": generate_password_hash("student123"),
        "role": "student",
    },
}


def load_users():
    if USER_FILE.exists():
        try:
            with USER_FILE.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            pass

    with USER_FILE.open("w", encoding="utf-8") as handle:
        json.dump(DEFAULT_USERS, handle, indent=2)
    return DEFAULT_USERS.copy()


def save_users(users):
    with USER_FILE.open("w", encoding="utf-8") as handle:
        json.dump(users, handle, indent=2)


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
        "preview_text": data.head(8).to_string(index=False),
    }


class StudentPerformanceGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Performance Predictor")
        self.geometry("760x560")
        self.config(bg="#f4f7fb")
        self.resizable(False, False)

        self.users = load_users()
        self.current_user = None

        try:
            self.data = pd.read_csv(DATA_FILE)
        except FileNotFoundError:
            messagebox.showerror("Missing dataset", f"Could not find {DATA_FILE}")
            self.destroy()
            return

        self.model_data = train_model(self.data)
        self.main_frame = tk.Frame(self, bg="#f4f7fb")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.show_login()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Login", font=("Inter", 22, "bold"), bg="#f4f7fb").pack(pady=(10, 20))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.build_input("Username", self.username_var)
        self.build_input("Password", self.password_var, True)

        tk.Button(self.main_frame, text="Sign In", command=self.try_login, bg="#2563eb", fg="#ffffff", font=("Inter", 11, "bold"), padx=14, pady=10).pack(pady=12)
        tk.Button(self.main_frame, text="Register a new account", command=self.show_register, bg="#e2e8f0", fg="#111827", font=("Inter", 10), padx=12, pady=8).pack(pady=4)

    def build_input(self, label_text, variable, is_password=False):
        tk.Label(self.main_frame, text=label_text, bg="#f4f7fb", font=("Inter", 11)).pack(anchor="w", pady=(8, 4))
        tk.Entry(self.main_frame, textvariable=variable, show="*" if is_password else "", font=("Inter", 11), width=32, bd=1, relief="solid").pack()

    def try_login(self):
        username = self.username_var.get().strip().lower()
        password = self.password_var.get()
        user = self.users.get(username)
        if user and check_password_hash(user["password"], password):
            self.current_user = username
            self.current_role = user["role"]
            self.show_dashboard()
        else:
            messagebox.showerror("Login failed", "Invalid username or password.")

    def show_register(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Register", font=("Inter", 22, "bold"), bg="#f4f7fb").pack(pady=(10, 20))

        self.reg_username = tk.StringVar()
        self.reg_password = tk.StringVar()
        self.reg_confirm = tk.StringVar()
        self.reg_role = tk.StringVar(value="student")

        self.build_input("Username", self.reg_username)
        self.build_input("Password", self.reg_password, True)
        self.build_input("Confirm Password", self.reg_confirm, True)

        tk.Label(self.main_frame, text="Role", bg="#f4f7fb", font=("Inter", 11)).pack(anchor="w", pady=(8, 4))
        role_menu = tk.OptionMenu(self.main_frame, self.reg_role, "student", "teacher")
        role_menu.config(width=30, font=("Inter", 11))
        role_menu.pack()

        tk.Button(self.main_frame, text="Create Account", command=self.create_account, bg="#2563eb", fg="#ffffff", font=("Inter", 11, "bold"), padx=14, pady=10).pack(pady=12)
        tk.Button(self.main_frame, text="Back to login", command=self.show_login, bg="#e2e8f0", fg="#111827", font=("Inter", 10), padx=12, pady=8).pack(pady=4)

    def create_account(self):
        username = self.reg_username.get().strip().lower()
        password = self.reg_password.get()
        confirm_password = self.reg_confirm.get()
        role = self.reg_role.get()

        if not username or not password or password != confirm_password:
            messagebox.showwarning("Registration error", "Please enter a valid username and matching passwords.")
            return
        if username in self.users:
            messagebox.showwarning("Registration error", "That username already exists.")
            return

        self.users[username] = {
            "password": generate_password_hash(password),
            "role": role,
        }
        save_users(self.users)
        messagebox.showinfo("Success", "Account created successfully. You can now sign in.")
        self.show_login()

    def show_dashboard(self):
        self.clear_frame()
        tk.Label(self.main_frame, text=f"Welcome, {self.current_user.capitalize()}", font=("Inter", 20, "bold"), bg="#f4f7fb").pack(pady=(10, 12))
        tk.Label(self.main_frame, text=f"Role: {self.current_role.capitalize()}", font=("Inter", 12), bg="#f4f7fb").pack(pady=(0, 16))

        stats_frame = tk.Frame(self.main_frame, bg="#f4f7fb")
        stats_frame.pack(fill="x", padx=4)

        self.build_stat_card(stats_frame, "Training samples", self.model_data["row_count"]).grid(row=0, column=0, padx=6)
        self.build_stat_card(stats_frame, "Mean Absolute Error", self.model_data["mae"]).grid(row=0, column=1, padx=6)
        self.build_stat_card(stats_frame, "R² Score", self.model_data["r2"]).grid(row=0, column=2, padx=6)

        frame_buttons = tk.Frame(self.main_frame, bg="#f4f7fb")
        frame_buttons.pack(pady=16)
        tk.Button(frame_buttons, text="Make a prediction", command=self.show_predict, bg="#2563eb", fg="#ffffff", font=("Inter", 11, "bold"), padx=14, pady=10).pack(side="left", padx=8)
        tk.Button(frame_buttons, text="Logout", command=self.logout, bg="#ef4444", fg="#ffffff", font=("Inter", 11, "bold"), padx=14, pady=10).pack(side="left", padx=8)

        tk.Label(self.main_frame, text="Dataset preview", font=("Inter", 14, "bold"), bg="#f4f7fb").pack(anchor="w", pady=(8, 4))
        preview_text = tk.Text(self.main_frame, height=10, width=84, font=("Consolas", 10), bd=1, relief="solid")
        preview_text.insert("1.0", self.model_data["preview_text"])
        preview_text.configure(state="disabled")
        preview_text.pack()

    def build_stat_card(self, parent, title, value):
        card = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid", padx=14, pady=12)
        tk.Label(card, text=title, font=("Inter", 11, "bold"), bg="#ffffff").pack(anchor="w")
        tk.Label(card, text=value, font=("Inter", 18, "bold"), bg="#ffffff", fg="#2563eb").pack(anchor="w", pady=(8, 0))
        return card

    def show_predict(self):
        self.clear_frame()
        tk.Label(self.main_frame, text="Predict Student Marks", font=("Inter", 20, "bold"), bg="#f4f7fb").pack(pady=(10, 16))

        self.predict_vars = {
            "study_hours": tk.StringVar(value="5"),
            "attendance": tk.StringVar(value="80"),
            "assignments_score": tk.StringVar(value="75"),
            "participation": tk.StringVar(value="6"),
            "previous_grade": tk.StringVar(value="70"),
        }

        form_frame = tk.Frame(self.main_frame, bg="#f4f7fb")
        form_frame.pack(pady=8)

        self.build_pred_input(form_frame, "Study Hours", self.predict_vars["study_hours"]).grid(row=0, column=0, padx=12, pady=6)
        self.build_pred_input(form_frame, "Attendance (%)", self.predict_vars["attendance"]).grid(row=0, column=1, padx=12, pady=6)
        self.build_pred_input(form_frame, "Assignments Score", self.predict_vars["assignments_score"]).grid(row=1, column=0, padx=12, pady=6)
        self.build_pred_input(form_frame, "Participation", self.predict_vars["participation"]).grid(row=1, column=1, padx=12, pady=6)
        self.build_pred_input(form_frame, "Previous Grade", self.predict_vars["previous_grade"]).grid(row=2, column=0, padx=12, pady=6)

        self.result_label = tk.Label(self.main_frame, text="", bg="#f4f7fb", font=("Inter", 16, "bold"), fg="#111827")
        self.result_label.pack(pady=12)

        bottom_frame = tk.Frame(self.main_frame, bg="#f4f7fb")
        bottom_frame.pack(pady=6)
        tk.Button(bottom_frame, text="Predict", command=self.predict_marks, bg="#2563eb", fg="#ffffff", font=("Inter", 11, "bold"), padx=14, pady=10).pack(side="left", padx=8)
        tk.Button(bottom_frame, text="Back", command=self.show_dashboard, bg="#e2e8f0", fg="#111827", font=("Inter", 11), padx=14, pady=10).pack(side="left", padx=8)

    def build_pred_input(self, parent, label_text, variable):
        frame = tk.Frame(parent, bg="#f4f7fb")
        tk.Label(frame, text=label_text, bg="#f4f7fb", font=("Inter", 11)).pack(anchor="w", pady=(0, 4))
        tk.Entry(frame, textvariable=variable, font=("Inter", 11), width=20, bd=1, relief="solid").pack()
        return frame

    def predict_marks(self):
        try:
            values = [
                float(self.predict_vars["study_hours"].get()),
                float(self.predict_vars["attendance"].get()),
                float(self.predict_vars["assignments_score"].get()),
                float(self.predict_vars["participation"].get()),
                float(self.predict_vars["previous_grade"].get()),
            ]
            prediction = self.model_data["model"].predict([values])[0]
            self.result_label.config(text=f"Estimated Marks: {prediction:.1f}")
        except ValueError:
            messagebox.showwarning("Input error", "Please enter numeric values in all fields.")

    def logout(self):
        self.current_user = None
        self.show_login()


if __name__ == "__main__":
    app = StudentPerformanceGUI()
    app.mainloop()
