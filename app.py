import sqlite3
from flask import Flask, request, redirect, render_template, url_for
from pathlib import Path

app = Flask(__name__, template_folder='HTML')
DB = Path("website.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS users (user_name TEXT, password TEXT)")
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return redirect(url_for("login_page"))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return "Login successful"
        else:
            return "Invalid username or password"

    return render_template("login.html") 

if __name__ == '__main__':
    init_db()
    app.run(debug=True)