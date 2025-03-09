from flask import Flask, render_template, request, redirect, jsonify, flash, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import random
import os

app = Flask(__name__)
app.secret_key = 'sydneytechnicalhighschool'  
DATABASE = os.path.join(os.path.dirname(__file__), 'database1.db')
logged_in = False

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
movies = conn.execute('SELECT * FROM Movies').fetchall()
movies_sorted = movies
conn.close()

@app.route("/")
def home():
    global genre_lock
    genre_lock = False
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM Movies').fetchall()
    # Format the release date for each movie
    formatted_movies = []
    for movie in movies:
        formatted_movie = dict(movie)
        formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
        formatted_movies.append(formatted_movie)
    conn.close()
    conn = get_db_connection()
    shuffled_movies =  conn.execute('SELECT * FROM Movies').fetchall()
    conn.close()
    if logged_in:
        recommended_movies = []

        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch all columns (genres) for the user
        query = 'SELECT animation, action, adventure, comedy, crime, drama, "sci-fi", mystery, biography, history, horror, thriller FROM Accounts WHERE username = ?'
        cursor.execute(query, (user,))
        result = cursor.fetchone()

        # Map the genres to their corresponding point values
        genres = ['animation', 'action', 'adventure', 'comedy', 'crime', 'drama', 'sci_fi', 'mystery', 'biography', 'history', 'horror', 'thriller']
        genre_points = dict(zip(genres, result))

        sorted_genre_points = sorted(genre_points.items(), key=lambda x: x[1], reverse=True)
        sorted_genre_points = sorted_genre_points[0:1]

        for i in formatted_movies:
            for x in sorted_genre_points:
                print(i['genre'].split(', '))
                print(x[0])
                if x[0] in i['genre'].lower().split(', ') and i not in recommended_movies:
                    recommended_movies.append(i)
        print(recommended_movies)
        conn.close()

    random.shuffle(shuffled_movies) # shuffles the movies to display in a random order
    if logged_in:
        return render_template("index.html", movies=formatted_movies, shuffled_movies=shuffled_movies[0:5], recommended_movies=recommended_movies)
    else:
        return render_template("index.html", movies=formatted_movies, shuffled_movies=shuffled_movies[0:5], recommended_movies=formatted_movies)

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route("/movies")
def movies():
    conn = get_db_connection()
    movies_sorted = conn.execute('SELECT * FROM Movies').fetchall()
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
genre_lock = False
genre_hold = ""

@app.route("/sort_movie", methods=["POST"])
def sort_movie():
    global movies_sorted
    global toggle_rating
    global toggle_release
    global toggle_name
    global previous_order
    global genre_lock
    global genre_hold

    order = request.form["order"]  # determining which button was pressed to sort the movies by
    conn = get_db_connection()
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
    else:
        movies_sorted = conn.execute(f'SELECT * FROM Movies WHERE genre LIKE "%{order}%"').fetchall()
        genre_lock = True
        genre_hold = order
        if order == "id":
            movies_sorted = conn.execute(f'SELECT * FROM Movies').fetchall()
            genre_lock = False
        conn.close()

    
    if order in ["rating", "release", "name"]:
        if genre_lock:
            conn = get_db_connection()
            movies_sorted = conn.execute('SELECT * FROM Movies WHERE genre LIKE ? ORDER BY {} {}'.format(order, toggle), ('%' + genre_hold + '%',) ).fetchall() # if the previous order was a genre, sort the movies by the genre and then by the button pressed
            conn.close()
        else:
            conn = get_db_connection()
            movies_sorted = conn.execute(f'SELECT * FROM Movies ORDER BY {order} {toggle}').fetchall()  # alter the SQL query based on the button pressed and whether it was ascending or descending
            conn.close()

    conn.close()
    print(order, toggle_rating, toggle_release, toggle_name)
    print(previous_order)

    previous_order = order

    # Convert the sorted movies to a list of dictionaries
    rendered_html = render_template('movies_sort_template.html', movies=movies_sorted) # uses the sorted movies to render the movies.html template
    return jsonify({'html': rendered_html}) # returns the rendered template of the sorted movies html $.ajax function in scripts.js

@app.route("/movies/<int:movie_id>", methods=["GET"])
def movie_details(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM Movies WHERE id = ?', (movie_id,)).fetchone()
    movie_genres = conn.execute('SELECT * FROM Movies').fetchall()

    conn.close()
    
    if movie is None:
        return "Movie not found", 404
    
    movielist = []
    genre_points = {}

    for i in movie_genres:
        for genre in i['genre'].split(', '):
            if genre in movie['genre'].split(', '): # split the genres from string (genre1, genre2, genre3) to tuple ['genre1', 'genre2', 'genre3']
                if i != movie:
                    if i not in genre_points:
                        genre_points[i] = 1
                    else:
                        genre_points[i] += 1

    
    sorted_genre = dict(sorted(genre_points.items(), key=lambda item: item[1], reverse=True))
    print(sorted_genre)
    for i in sorted_genre:
        if sorted_genre[i] >= (len(movie['genre'].split(', '))-1):
            movielist.append(i)

    print(movielist)

    # code for adding genre "points" to account for movie reccomendations

    if logged_in:
        for i in [g.strip() for g in movie['genre'].split(',')]:
            conn = get_db_connection()
            # Fetch the current value of the genre category
            cursor = conn.execute(f'SELECT "{i}" FROM Accounts WHERE username = ?', (user,))
            current_value = cursor.fetchone()

            # Check if the value exists
            if current_value is not None:
                current_value = current_value[0] or 0  # Handle NULL values as 0
                new_value = current_value + 1 # increments value by one

                # Update the column by incrementing its value
                conn.execute(f'UPDATE Accounts SET "{i}" = ? WHERE username = ?', (new_value, user))
                conn.commit()

            conn.close()



    
    formatted_movie = dict(movie)
    formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
    
    return render_template("movie_details.html", movie=formatted_movie, movies=movielist)

@app.route('/search', methods=['GET'])
def search():
    # Get the value of the "search" input field
    query = request.args.get('search')
    # Process the query
    if query:
        conn = get_db_connection()
        movies = conn.execute("SELECT * FROM Movies WHERE name LIKE ?", ('%' + query + '%',)).fetchall()
        formatted_movies = []
        for movie in movies:
            formatted_movie = dict(movie)
            formatted_movie['release'] = datetime.strptime(movie['release'], "%Y-%m-%d").strftime("%Y")
            formatted_movies.append(formatted_movie)
        return render_template("movies.html", movies=formatted_movies)
    else:
        return 
    
@app.route('/account')
def account():
    global logged_in
    if logged_in:
        flash('You are already logged in!', 'info')  # Flash the message
        return redirect(url_for('home'))
    else:
        return render_template("login.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

from flask import flash, redirect, url_for

@app.route('/make_account', methods=['POST'])
def make_account():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    
    # Hash the password for security
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if the username already exists
        cursor.execute("SELECT username FROM Accounts WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Flash message for duplicate username
            flash("Account creation failed: Username already exists.", "danger")
            return redirect(url_for('signup'))  # Redirect to the sign-up page

        # SQL query to insert user data if username is unique
        query = "INSERT INTO Accounts (username, email, password) VALUES (?, ?, ?)"
        values = (username, email, hashed_password)
        cursor.execute(query, values)
        conn.commit()

        # Flash message for successful account creation
        flash("Account creation successful! Please sign in.", "success")
        return redirect(url_for('account'))  # Redirect to the sign-in page
    
    except Exception as e:
        # Handle any other exceptions
        flash(f"Account creation failed: {str(e)}", "danger")
        return redirect(url_for('signup'))  # Redirect to the sign-up page
    
    finally:
        # Close the database connection
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    global logged_in
    global user
    # Get the login credentials from the form
    username = request.form['username']
    password = request.form['password']
    
    # Fetch the stored hashed password for this username from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM Accounts WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        hashed_password = result[0]  # Extract the hashed password from the result
        
        # Compare the entered password with the hashed password
        if check_password_hash(hashed_password, password):
            flash("Login successful! Welcome back.", "success")  # Success message
            logged_in = True
            user = username
            return redirect(url_for('home'))  # Redirect to the home page
        else:
            flash("Invalid username or password. Please try again.", "danger")  # Error message
            return redirect(url_for('account'))  # Redirect back to the login page
    else:
        flash("User not found. Please check your credentials.", "danger")  # User not found message
        return redirect(url_for('account'))  
    
@app.route('/logout')
def logout():
    global logged_in
    global user
    logged_in = False
    user = ""
    return redirect(url_for("home"))

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS Movies
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    release DATE NOT NULL,
                    rating REAL NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Accounts
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL,
                    password TEXT NOT NULL,
                    animation INTEGER DEFAULT 0,
                    action INTEGER DEFAULT 0,
                    adventure INTEGER DEFAULT 0,
                    comedy INTEGER DEFAULT 0,
                    crime INTEGER DEFAULT 0,
                    drama INTEGER DEFAULT 0,
                    [sci-fi] INTEGER DEFAULT 0,
                    mystery INTEGER DEFAULT 0,
                    biography INTEGER DEFAULT 0,
                    history INTEGER DEFAULT 0,
                    horror INTEGER DEFAULT 0,
                    thriller INTEGER DEFAULT 0,
                    music INTEGER DEFAULT 0,
                    short INTEGER DEFAULT 0,
                    fantasy INTEGER DEFAULT 0)''')

    conn.close()
    app.run(debug=True)