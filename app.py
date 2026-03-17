from flask import Flask, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("website (1).db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/login', methods=['POST'])
def login():
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

if __name__ == '__main__':
    app.run(debug=True)
