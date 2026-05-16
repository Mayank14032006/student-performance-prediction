# Student Performance Prediction

This project is now a Flask web app with a login system, a richer dataset, and a modern GUI.

## Features
- Flask-based web interface for student marks prediction
- Login and registration system with session support
- Better dataset with additional features:
  - Study Hours
  - Attendance
  - Assignments Score
  - Participation
  - Previous Grade
- Linear Regression model trained at startup
- Responsive HTML GUI with dataset preview and prediction form

## Run locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Flask web app
2. Run the web app:
   ```bash
   python main.py
   ```
3. Open the browser at `http://127.0.0.1:5000`

### Desktop GUI app
2. Run the desktop app:
   ```bash
   python gui.py
   ```

## Default accounts
- teacher / password123
- student / student123

## Notes
- A new `users.json` file is created automatically the first time either app runs.
- Both the web and desktop apps use the improved dataset in `student_performance.csv`.
