from flask import Flask, render_template, request, redirect, jsonify
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

@app.route("/")
def home():
    conn = get_db_connection()
    global movies_sorted
    conn.close()
    
    # Format the release date for each movie
    formatted_movies = []
    for movie in movies_sorted:
        formatted_movie = dict(movie)
        formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
        formatted_movies.append(formatted_movie)
    
    shuffled_movies = formatted_movies

    random.shuffle(shuffled_movies) # shuffles the movies to display in a random order

    return render_template("index.html", movies=formatted_movies, shuffled_movies=shuffled_movies[0:5])

@app.route("/movies")
def movies():
    conn = get_db_connection()
    global movies_sorted
    movies_by_release = conn.execute('SELECT * FROM Movies ORDER BY release DESC').fetchall()
    movies_sorted_rating = conn.execute('SELECT * FROM Movies ORDER BY rating DESC').fetchall()
    conn.close()
    
    # Format the release date for each movie
    formatted_movies = []
    for movie in movies_sorted:
        formatted_movie = dict(movie)
        formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
        formatted_movies.append(formatted_movie) 
    
    return render_template("movies.html", movies=formatted_movies)

@app.route("/add_movie", methods=["POST"])
def add_movie():
    name = request.form["name"]
    release = request.form["release"]
    rating = float(request.form["rating"])  # Convert rating to float (decimal) for more precise ratings
    
    conn = get_db_connection()
    conn.execute("INSERT INTO Movies (name, release, rating) VALUES (?, ?, ?)",
                 (name, release, rating))
    conn.commit()
    conn.close()
    
    return redirect("/#heading")

# initialising the toggle values for sorting
# this avoids the need to sort the movies every time the page is refreshed
# since they are intialised in the database as values, and as global functions, they can be accessed and modified and won't be lost on page refresh
toggle_rating = "DESC"
toggle_release = "DESC"
toggle_name = "DESC"
previous_order = ""

@app.route("/sort_movie", methods=["POST"])
def sort_movie():
    global movies_sorted
    global toggle_rating
    global toggle_release
    global toggle_name
    global previous_order

    order = request.form["order"]  # determining which button was pressed to sort the movies by

    # main logic for toggling sorting based on which button was pressed
    if order == "rating":
        if previous_order == order:
            toggle_rating = "ASC" if toggle_rating == "DESC" else "DESC"
        toggle = toggle_rating
    elif order == "release":
        if previous_order == order:
            toggle_release = "ASC" if toggle_release == "DESC" else "DESC"
        toggle = toggle_release
    elif order == "name":
        if previous_order == order:
            toggle_name = "ASC" if toggle_name == "DESC" else "DESC"
        toggle = toggle_name

    conn = get_db_connection()
    movies_sorted = conn.execute(f'SELECT * FROM Movies ORDER BY {order} {toggle}').fetchall()  # alter the SQL query based on the button pressed and whether it was ascending or descending
    conn.close()

    previous_order = order

    # Convert the sorted movies to a list of dictionaries
    rendered_html = render_template('movies_sort_template.html', movies=movies_sorted) # uses the sorted movies to render the movies.html template
    return jsonify({'html': rendered_html}) # returns the rendered template of the sorted movies html $.ajax function in scripts.js

@app.route("/movies/<int:movie_id>", methods=["GET"])
def movie_details(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM Movies WHERE id = ?', (movie_id,)).fetchone()
    conn.close()
    
    if movie is None:
        return "Movie not found", 404
    
    formatted_movie = dict(movie)
    formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
    
    return render_template("movie_details.html", movie=formatted_movie)

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