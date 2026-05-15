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

    CREATE TABLE IF NOT EXISTS wishlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        UNIQUE(user_id, game_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(game_id) REFERENCES games(id)
    );
    """)

    if conn.execute("SELECT COUNT(*) FROM genre").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO genre (name) VALUES ('Action'), ('RPG'), ('Sports')")

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
            "SELECT * FROM users WHERE user_name=?",
            (username,)
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
            "SELECT * FROM users WHERE email=?",
            (email,)
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

    search = (request.args.get('search') or '').strip()

    conn = get_db()

    base_query = """
        SELECT games.*, genre.name AS genre
        FROM games
        JOIN genre ON games.genre_id = genre.id
    """

    if search:
        games = conn.execute(
            base_query + """
            WHERE LOWER(genre.name) LIKE ?
               OR LOWER(games.title) LIKE ?
               OR LOWER(games.developer) LIKE ?
            ORDER BY games.id DESC
            """,
            (f"%{search.lower()}%", f"%{search.lower()}%", f"%{search.lower()}%",)
        ).fetchall()
    else:
        games = conn.execute(base_query + " ORDER BY games.id DESC").fetchall()

    conn.close()

    return render_template("browse.html", games=games, search=search)


@app.route('/profile')
def profile():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    if not user:
        conn.close()
        return redirect(url_for("logout"))

    review_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM reviews WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()["cnt"]

    user_reviews = conn.execute("""
        SELECT reviews.rating, reviews.comment, games.title AS game_title

        FROM reviews
        JOIN games ON reviews.game_id = games.id
        WHERE reviews.user_id = ?
        ORDER BY reviews.id DESC
    """, (session["user_id"],)).fetchall()

    favourite_games = conn.execute("""
        SELECT games.id, games.title, genre.name AS genre
        FROM games
        JOIN genre ON games.genre_id = genre.id
        WHERE games.id IN (
            SELECT game_id FROM wishlist WHERE user_id = ?
        )
    """, (session["user_id"],)).fetchall()

    favourite_count = len(favourite_games)

    conn.close()

    user_dict = dict(user)
    user_dict.setdefault("created_at", "N/A")

    return render_template(
        "profile.html",
        user=user_dict,
        review_count=review_count,
        favourite_count=favourite_count,
        user_reviews=user_reviews,
        favourite_games=favourite_games
    )


@app.route('/add-wishlist/<int:game_id>')
def add_wishlist(game_id):
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO wishlist (user_id, game_id) VALUES (?, ?)",
        (session["user_id"], game_id)
    )
    conn.commit()
    conn.close()

    return redirect(request.referrer or url_for("browse_games"))


@app.route('/remove-wishlist/<int:game_id>')
def remove_wishlist(game_id):
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    conn = get_db()
    conn.execute(
        "DELETE FROM wishlist WHERE user_id = ? AND game_id = ?",
        (session["user_id"], game_id)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("profile"))


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

    is_favourite_row = conn.execute(
        "SELECT 1 FROM wishlist WHERE user_id = ? AND game_id = ?",
        (session["user_id"], game_id)
    ).fetchone()
    is_favourite = is_favourite_row is not None

    conn.close()

    return render_template(
        "game.html",
        game=game,
        reviews=reviews,
        avg_rating=round(avg_rating, 1) if avg_rating else "No ratings",
        is_favourite=is_favourite
    )


@app.route('/add_review/<int:game_id>', methods=['POST'])
def add_review(game_id):
    # Ensure incoming form data matches the DB schema.
    # In this project the reviews table column is `comment` and it is NOT NULL.

    if "user_id" not in session:
        return redirect(url_for("login_page"))

    rating = request.form.get('rating')
    comment = request.form.get('review', '')

    # Reviews table in this project uses NOT NULL column `review_text`
    if comment is None:
        comment = ''

    if not str(comment).strip():
        return redirect(url_for('game_page', game_id=game_id))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO reviews (user_id, game_id, rating, review_text, comment, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """,
        (session['user_id'], game_id, rating, comment.strip(), comment.strip())
    )

    conn.commit()
    conn.close()

    return redirect(url_for('game_page', game_id=game_id))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)