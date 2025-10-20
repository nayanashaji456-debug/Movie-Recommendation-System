import pickle
import pandas as pd
import numpy as np
import requests
import os
import functools
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


movies = None
similarity = None
USERS_FILE = 'data/users.pkl'
API_KEY = "831dc5cf6ed482400a217ee7228961a1"
PLACEHOLDER_POSTER = "https://placehold.co/300x450/333/FFFFFF?text=No+Poster"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'rb') as f:
            return pickle.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'wb') as f:
        pickle.dump(users, f)

users = load_users()


def fetch_poster(movie_id):
    if not movie_id or movie_id == 0:
        return PLACEHOLDER_POSTER
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
        data = requests.get(url, timeout=5).json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except:
        pass
    return PLACEHOLDER_POSTER

#  Load movie data 
def load_data():
    global movies, similarity
    try:
        movies_dict = pickle.load(open('data/movie_dict.pkl', 'rb'))
        movies = pd.DataFrame(movies_dict)
        similarity = pickle.load(open('data/similarity.pkl', 'rb'))
    except Exception:
        # Fallback data
        movies = pd.DataFrame([
            {'title': 'Inception', 'movie_id': 27205, 'year': 2010, 'vote_average': 8.8, 'description': 'Mind-bending dream sequences.'},
            {'title': 'The Dark Knight', 'movie_id': 155, 'year': 2008, 'vote_average': 8.5, 'description': 'Batman faces the Joker.'},
            {'title': 'Interstellar', 'movie_id': 157336, 'year': 2014, 'vote_average': 8.6, 'description': 'A mission beyond our solar system.'},
            {'title': 'Pulp Fiction', 'movie_id': 680, 'year': 1994, 'vote_average': 8.9, 'description': 'Intertwining tales of LA crime.'},
            {'title': 'Fight Club', 'movie_id': 550, 'year': 1999, 'vote_average': 8.7, 'description': 'The first rule about Fight Club is...'},
        ])
        N = len(movies)
        similarity = np.random.rand(N, N)
        np.fill_diagonal(similarity, 1.0)

load_data()

# Fetch movie details
def fetch_movie_details(movie_id):
    details = {
        "title": "Unknown",
        "poster": PLACEHOLDER_POSTER,
        "description": "Description not available.",
        "year": "N/A",
        "vote_average": "N/A",
        "cast": []
    }
    if not movie_id or movie_id == 0:
        return details
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&append_to_response=credits"
        data = requests.get(url, timeout=5).json()
        if data.get('status_code') == 34:
            return details
        details['title'] = data.get("title", details['title'])
        details['poster'] = f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else PLACEHOLDER_POSTER
        details['description'] = data.get("overview", details['description'])
        details['year'] = data.get("release_date", "N/A")[:4] if data.get("release_date") else "N/A"
        details['vote_average'] = data.get("vote_average", details['vote_average'])
        credits = data.get('credits', {})
        if credits.get('cast'):
            details['cast'] = [c['name'] for c in credits['cast'][:5]]
    except Exception as e:
        print("TMDb fetch error:", e)
    return details

def recommend(movie_title):
    if movies is None or similarity is None:
        return []
    try:
        index = movies[movies['title'] == movie_title].index[0]
    except IndexError:
        return []
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movies = []
    for i in distances[1:6]:
        movie_data = movies.iloc[i[0]]
        recommended_movies.append({
            'title': movie_data.get('title', 'Unknown'),
            'poster': fetch_poster(movie_data.get('movie_id')),
            'year': movie_data.get('year', 'N/A'),
            'vote_average': movie_data.get('vote_average', 'N/A'),
            'movie_id': movie_data.get('movie_id', 0)
        })
    return recommended_movies


def requires_login(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return wrapper



# Welcome page
@app.route('/')
def welcome_page():
    if session.get('logged_in'):
        if 'language' not in session:
            return redirect(url_for('language_select_page'))
        return redirect(url_for('home_page'))
    return render_template('welcome.html')

# Register page
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return render_template('register.html', error="Please fill in all fields.")
        if email in users:
            return render_template('register.html', error="Email already registered.")
        hashed_pw = generate_password_hash(password)
        users[email] = hashed_pw
        save_users(users)
        return redirect(url_for('login_page'))
    return render_template('register.html', error=None)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_pw = users.get(email)
        if user_pw and check_password_hash(user_pw, password):
            session['logged_in'] = True
            session['username'] = email
            return redirect(url_for('language_select_page'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html', error=None)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('welcome_page'))

# Language selection
@app.route('/language', methods=['GET'])
@requires_login
def language_select_page():
    if 'language' in session:
        return redirect(url_for('home_page'))
    return render_template('language_select.html')

@app.route('/set_language', methods=['POST'])
@requires_login
def set_language():
    session['language'] = request.form.get('selected_language', 'en')
    return redirect(url_for('home_page'))

# Home page
@app.route('/home', methods=['GET'])
@requires_login
def home_page():
    movie_list = movies.sample(n=min(50, len(movies))).copy()
    movie_list['poster'] = movie_list['movie_id'].apply(fetch_poster)
    movie_list = movie_list.to_dict(orient='records')
    return render_template('home.html', username=session['username'], movie_list=movie_list, current_language=session.get('language', 'en'))

# Search movies
@app.route('/search', methods=['POST'])
@requires_login
def search_movie():
    query = request.form.get('query', '').lower()
    if not query:
        return redirect(url_for('home_page'))
    filtered_movies = movies[movies['title'].str.lower().str.contains(query)].copy()
    filtered_movies['poster'] = filtered_movies['movie_id'].apply(fetch_poster)
    filtered_movies = filtered_movies.to_dict(orient='records')
    return render_template('home.html', username=session['username'], movie_list=filtered_movies, search_query=query)

# Movie details
@app.route('/movie/<int:movie_id>')
@requires_login
def movie_detail_page(movie_id):
    movie = fetch_movie_details(movie_id)
    recommendations = recommend(movie['title']) if movie else []
    return render_template('movie_detail.html', movie=movie, recommendations=recommendations, username=session['username'])


if __name__ == '__main__':
    app.run(debug=True, port=5000)
