import sqlite3
from flask import Flask, request, redirect, render_template, url_for, flash
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='HTML')
app.secret_key = "gamelens_secret_key"
DB = Path("website.db")

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS genre (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        genre_id INTEGER NOT NULL,
        developer TEXT NOT NULL,
        release_date DATETIME NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        cover_image_url TEXT,
        FOREIGN KEY (genre_id) REFERENCES genre (id)
    );
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return redirect(url_for("login_page"))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE user_name=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            return "Login successful"
        else:
            return "Invalid username or password"
            
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)
        
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (user_name, email, password, role) VALUES (?, ?, ?, ?)",
                         (username, email, hashed_pw, 'user'))
            conn.commit()
            conn.close()
            return redirect(url_for('login_page'))
        except sqlite3.IntegrityError:
            return "Registration failed: User already exists"

    return render_template("register.html")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        
        if user:
            return f"Password reset link sent to {email}"
        else:
            return "Email not found"
            
    return render_template("forgot_password.html")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)