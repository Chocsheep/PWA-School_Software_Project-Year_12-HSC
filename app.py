from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import random
import os

app = Flask(__name__)
DATABASE = os.path.join(os.path.dirname(__file__), 'database1.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
movies = conn.execute('SELECT * FROM Movies').fetchall()
movies_sorted = movies

asc_desc = "DESC"
previous_order = ""

@app.route("/")
def home():
    conn = get_db_connection()
    global movies_sorted
    movies_by_release = conn.execute('SELECT * FROM Movies ORDER BY release DESC').fetchall()
    movies_sorted_rating = conn.execute('SELECT * FROM Movies ORDER BY rating DESC').fetchall()
    conn.close()
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format the release date for each movie
    formatted_movies = []
    for movie in movies_sorted:
        formatted_movie = dict(movie)
        formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
        formatted_movies.append(formatted_movie)
    
    return render_template("index.html", today=today, movies=formatted_movies)

@app.route("/add_movie", methods=["POST"])
def add_movie():
    name = request.form["name"]
    release = request.form["release"]
    rating = float(request.form["rating"])  # Convert rating to float
    
    conn = get_db_connection()
    conn.execute("INSERT INTO Movies (name, release, rating) VALUES (?, ?, ?)",
                 (name, release, rating))
    conn.commit()
    conn.close()
    
    return redirect("/#heading")

@app.route("/sort_movie", methods=["POST"])
def sort_movie():    
    conn = get_db_connection()
    global asc_desc
    global movies_sorted
    global previous_order
    order = request.form["order"]
    if asc_desc == "ASC" and previous_order == order:
        asc_desc = "DESC"
    elif asc_desc == "DESC" and previous_order == order:
        asc_desc = "ASC"
    movies_sorted = conn.execute(f'SELECT * FROM Movies ORDER BY {order} {asc_desc}').fetchall()
    previous_order = order
    conn.close()
    
    return redirect("/#heading")

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS Movies
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    release DATE NOT NULL,
                    rating REAL NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()
    app.run(debug=True)