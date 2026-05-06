import sqlite3
from flask import Flask, request, redirect, render_template, url_for, session
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
        release_date TEXT NOT NULL,
        price INTEGER NOT NULL,
        description TEXT,
        cover_image_url TEXT,
        FOREIGN KEY (genre_id) REFERENCES genre (id)
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        game_id INTEGER,
        rating INTEGER,
        comment TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (game_id) REFERENCES games(id)
    );
    """)

    if conn.execute("SELECT COUNT(*) FROM genre").fetchone()[0] == 0:
        conn.execute("INSERT INTO genre (name) VALUES ('Action'), ('RPG'), ('Sports')")

    if conn.execute("SELECT COUNT(*) FROM games").fetchone()[0] == 0:
        conn.execute("""
            INSERT INTO games (title, genre_id, developer, release_date, price, description)
            VALUES
            ('CyberQuest', 1, 'Nova Studios', '2024', 60, 'Futuristic action game'),
            ('Dragon Realm', 2, 'Mythic Devs', '2023', 70, 'Open world RPG'),
            ('Pro Football 25', 3, 'SportX', '2025', 50, 'Realistic sports game')
        """)

    conn.commit()
    conn.close()


@app.route("/", methods=['GET'])
def home():
    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE user_name=?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['user_name']
            return redirect(url_for('browse_games'))

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
            conn.execute(
                "INSERT INTO users (user_name, email, password, role) VALUES (?, ?, ?, ?)",
                (username, email, hashed_pw, 'user')
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login_page'))

        except sqlite3.IntegrityError:
            return "User already exists"

    return render_template("register.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        conn.close()

        if user:
            return f"Reset link sent to {email}"
        return "Email not found"

    return render_template("forgot_password.html")



@app.route('/browse')
def browse_games():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = get_db()
    games = conn.execute("""
        SELECT games.*, genre.name AS genre
        FROM games
        JOIN genre ON games.genre_id = genre.id
    """).fetchall()
    conn.close()

    return render_template("browse.html", games=games)



@app.route('/game/<int:game_id>')
def game_page(game_id):
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = get_db()

    game = conn.execute("""
        SELECT games.*, genre.name AS genre
        FROM games
        JOIN genre ON games.genre_id = genre.id
        WHERE games.id = ?
    """, (game_id,)).fetchone()

    reviews = conn.execute("""
        SELECT reviews.*, users.user_name AS username
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE game_id = ?
    """, (game_id,)).fetchall()

    avg_rating = conn.execute("""
        SELECT AVG(rating) as avg FROM reviews WHERE game_id = ?
    """, (game_id,)).fetchone()["avg"]

    conn.close()

    return render_template(
        "game.html",
        game=game,
        reviews=reviews,
        avg_rating=round(avg_rating, 1) if avg_rating else "No ratings"
    )

@app.route('/add-review', methods=['GET', 'POST'])
def add_review_page():
    if request.method == 'GET':
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("add_review.html")

    # POST
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    game_title = request.form.get('game')
    rating = request.form.get('rating')
    review_text = request.form.get('review')

    conn = get_db()
    game = conn.execute("SELECT id FROM games WHERE title = ?", (game_title,)).fetchone()
    if not game:
        conn.close()
        return "Game not found. Use exact name like 'CyberQuest'."

    game_id = game['id']
    
    try:
        conn.execute("""
        INSERT INTO reviews (user_id, game_id, rating, comment)
            VALUES (?, ?, ?, ?)
        """, (session['user_id'], game_id, int(rating), review_text))
        if not review_text or not review_text.strip():
            conn.close()
            return "Review cannot be empty"

        conn.commit()
    except Exception as e:
        conn.close()
        return f"Error: {str(e)}"
    conn.close()

    return redirect(url_for('game_page', game_id=game_id))


@app.route('/add_review/<int:game_id>', methods=['POST'])
def add_review(game_id):
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    rating = request.form.get('rating')
    comment = request.form.get('review')

    conn = get_db()
    conn.execute("""
        INSERT INTO reviews (user_id, game_id, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (session['user_id'], game_id, rating, comment))

    conn.commit()
    conn.close()

    return redirect(url_for('game_page', game_id=game_id))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
