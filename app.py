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

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS Movies
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    rating TEXT NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()
    app.run(debug=True)