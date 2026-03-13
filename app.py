from flask import Flask, render_template, request, redirect, url_for,session
import sqlite3
from datetime import date
import calendar
from werkzeug.security import generate_password_hash, check_password_hash  #ハッシュ化を使えるようにする。

app = Flask(__name__)
app.secret_key = 'your_secret_key'  #セッションを安全に保つためのキー

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            time INTEGER NOT NULL,
            study_date TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()



@app.route('/', methods=['GET', 'POST'])
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    conn = get_db_connection()

    if request.method == 'POST':
        study_time = int(request.form['time'])
        content = request.form['content']
        custom_content = request.form['custom_content']
        study_date = request.form['study_date']

        if content == "other" and custom_content:
            content = custom_content


        if not study_date:
            study_date = date.today().isoformat()
        
        if study_time and content:
            conn.execute(
                "INSERT INTO logs (user_id, content, time, study_date) VALUES (?, ?, ?, ?)",
                (session["user_id"], content, int(study_time), study_date)
            )
            conn.commit()

        conn.close()
        return redirect(url_for('home'))

    logs = conn.execute(
    "SELECT * FROM logs WHERE user_id = ? ORDER BY study_date DESC",
    (session["user_id"],)
    ).fetchall()

    selected_date = request.args.get("selected_date")
    selected_logs = []

    if selected_date:
            selected_logs = conn.execute(
                "SELECT * FROM logs WHERE study_date = ? AND user_id = ? ORDER BY id DESC",
                (selected_date, session["user_id"])
            ).fetchall()

    today_obj = date.today()
    year = today_obj.year
    month = today_obj.month

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    study_dates = conn.execute(
    """
    SELECT DISTINCT study_date
    FROM logs
    WHERE user_id = ?
    AND strftime('%Y-%m', study_date) = ?
    """,
    (session["user_id"], f"{year}-{month:02d}")
).fetchall()

    study_dates = [row["study_date"] for row in study_dates]

    
    total_time = conn.execute(
    "SELECT SUM(time) AS total FROM logs WHERE user_id = ?",
    (session["user_id"],)
).fetchone()["total"] or 0

    weekly_total = conn.execute("""
        SELECT SUM(time) AS total
        FROM logs
        WHERE user_id = ?
        AND study_date >= date('now', 'weekday 1', '-7 days')
        AND study_date < date('now', 'weekday 1')
    """, (session["user_id"],)).fetchone()["total"] or 0

    monthly_total = conn.execute("""
        SELECT SUM(time) AS total
        FROM logs
        WHERE user_id = ?
        AND strftime('%Y-%m', study_date) = strftime('%Y-%m', 'now')
    """, (session["user_id"],)).fetchone()["total"] or 0

    weekly_avg = round(weekly_total / 7, 1)
    monthly_avg = round(monthly_total / date.today().day, 1)

    conn.close()

    
    return render_template(
    'index.html',
    logs=logs,
    total_time=total_time,
    weekly_total=weekly_total,
    monthly_total=monthly_total,
    weekly_avg=weekly_avg,
    monthly_avg=monthly_avg,
    year=year,
    month=month,
    month_days=month_days,
    study_dates=study_dates,
    today=today_obj.isoformat(),
    selected_date=selected_date,
    selected_logs=selected_logs,
    )


@app.route("/delete/<int:log_id>", methods=["POST"])
def delete(log_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM logs WHERE id = ? AND user_id = ?", (log_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


@app.route("/edit/<int:log_id>", methods=["GET", "POST"])
def edit(log_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()

    if request.method == "POST":
        study_date = request.form["date"]
        content = request.form["content"]
        study_time = request.form["time"]

        conn.execute(
            "UPDATE logs SET study_date = ?, content = ?, time = ? WHERE id = ? AND user_id = ?",
            (study_date, content, study_time, log_id, session["user_id"])
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    log = conn.execute(
        "SELECT * FROM logs WHERE id = ? AND user_id = ?",
        (log_id, session["user_id"])
    ).fetchone()
    conn.close()
    if log is None:
        return"このデータにはアクセスできません"

    return render_template("edit.html", log=log)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_user:
            conn.close()
            return "このユーザー名はすでに使われています"

        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        else:
            return "ユーザー名またはパスワードが違います"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add")
def add():
    return "<h2>Add Study Log Page</h2>"


if __name__ == '__main__':
    init_db()
    app.run(debug=True)