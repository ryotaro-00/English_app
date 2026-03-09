from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
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

def add_date_column():
    conn = get_db_connection()
    conn.execute("ALTER TABLE logs ADD COLUMN study_date TEXT")
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def home():
    conn = get_db_connection()

    if request.method == 'POST':
        study_time = int(request.form['time'])
        content = request.form['content']

        if study_time and content:
            today = date.today().isoformat()
            conn.execute(
                "INSERT INTO logs (content, time,study_date) VALUES (?, ?, ?)",
                (content, int(study_time),today)
            )
            conn.commit()

        conn.close()
        return redirect(url_for('home'))

    logs = conn.execute("SELECT * FROM logs ORDER BY study_date DESC").fetchall()
    conn.close()

    return render_template('index.html', logs=logs)


@app.route("/delete/<int:log_id>", methods=["POST"])
def delete(log_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


@app.route("/edit/<int:log_id>", methods=["GET", "POST"])
def edit(log_id):
    conn = get_db_connection()

    if request.method == "POST":
        study_date = request.form["date"]
        content = request.form["content"]
        study_time = request.form["time"]

        conn.execute(
            "UPDATE logs SET study_date = ?, content = ?, time = ? WHERE id = ?",
            (study_date, content, study_time, log_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("home"))

    log = conn.execute(
        "SELECT * FROM logs WHERE id = ?",
        (log_id,)
    ).fetchone()
    conn.close()

    return render_template("edit.html", log=log)


@app.route("/add")
def add():
    return "<h2>Add Study Log Page</h2>"


if __name__ == '__main__':
    init_db()
    app.run(debug=True)