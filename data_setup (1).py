import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Paths
MOVIES_CSV = 'tmdb_5000_movies.csv'
CREDITS_CSV = 'tmdb_5000_credits.csv'
ARTIFACTS_DIR = 'artifacts'
MOVIE_DICT_PKL = os.path.join(ARTIFACTS_DIR, 'movie_dict.pkl')
SIMILARITY_PKL = os.path.join(ARTIFACTS_DIR, 'similarity.pkl')

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# 1) Load CSVs
print("Loading CSV files...")
movies = pd.read_csv(MOVIES_CSV)
credits = pd.read_csv(CREDITS_CSV)

# 2) Merge datasets
print("Merging datasets...")
df = movies.merge(credits, on='title', how='left')

# 3) Keep useful columns
if 'id' in df.columns:
    df.rename(columns={'id': 'movie_id'}, inplace=True)

df['description'] = df['overview'].fillna('')
df['poster_path'] = df['poster_path'].fillna('')

# release_date -> year
if 'release_date' in df.columns:
    df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
else:
    df['year'] = None

df = df[['title', 'movie_id', 'year', 'vote_average', 'description', 'poster_path']].drop_duplicates(subset=['title']).reset_index(drop=True)

# 4) Save movie_dict.pkl
movie_dict = df.to_dict(orient='list')
with open(MOVIE_DICT_PKL, 'wb') as f:
    pickle.dump(movie_dict, f)
print(f"Saved movie_dict.pkl with {len(df)} movies.")

# 5) Build TF-IDF similarity
print("Building TF-IDF and similarity matrix...")
tfidf = TfidfVectorizer(stop_words='english', max_features=20000)
tfidf_matrix = tfidf.fit_transform(df['description'].astype(str))
similarity = cosine_similarity(tfidf_matrix, tfidf_matrix)

# 6) Save similarity.pkl
with open(SIMILARITY_PKL, 'wb') as f:
    pickle.dump(similarity, f)
print(f"Saved similarity matrix with shape {similarity.shape}.")

print("✅ Done creating artifacts.")