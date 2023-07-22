#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from flask import Flask, render_template
from datetime import datetime
import pandas as pd
import openai
import random

app = Flask(__name__)

today = datetime.today()
matches = pd.read_csv(f"matches{today.strftime('%d%m%Y')}_IMDB.csv") 
# matches=pd.read_csv("matches29072023_IMDB.csv") # --- use if you want a specific csv

books = pd.read_csv("best_books.csv")
movies = pd.read_csv("imdb_movie_fetch.csv")

# Replace &apos; with '
matches = matches.replace("&apos;", "'", regex=True)
books = books.replace("&apos;", "'", regex=True)
movies = movies.replace("&apos;", "'", regex=True)

matches["Date"] = matches["Date"].str[:10]

@app.route('/')
def home():
    matches_today = matches

    international_days = matches_today[matches_today['Country'].notna()]
    birthdays = matches_today[matches_today['description'] == "birthday"]
    anniversaries = matches_today[(matches_today['Country'].isna()) & (matches_today['description'] != "birthday")]

    days_list = [international_days, birthdays, anniversaries]

    recommendations = []
    for days in days_list:
        if not days.empty:
            day = days.sample(1)
            for _, match in day.iterrows():
                movies_match = [movies[movies['title'] == match[f'match_movie{i+1}']] for i in range(3)]
                books_match = [books[books['title'] == match[f'match_book{i+1}']] for i in range(3)]

                movies_list = [movie_match.iloc[0] if not movie_match.empty else None for movie_match in movies_match]
                books_list = [book_match.iloc[0] if not book_match.empty else None for book_match in books_match]

                if any(movie is not None for movie in movies_list) or any(book is not None for book in books_list):
                    if pd.notna(match['Country']):
                        day_name = str(match["Name"]) + " (" + str(match["Country"])+ ")"
                        day_description = match['description']
                    elif match['description'] == "birthday":
                        day_name = "Birthday"
                        day_description = match["Name"] + " (" + match["Date"] + ")"
                    else:
                        day_name = match['Name'] + " (" + match["Date"] + ")"
                        day_description = match['description']
                    
                    recommendation_movies = []
                    for i, movie in enumerate(movies_list):
                        if movie is not None:
                            recommendation_movies.append({
                                'title': movie['title'],
                                'description': match[f'match_movie{i+1}_descr'],
                                'image': movie["image"] if pd.notna(movie["image"]) else None,
                                'rating': movie['rating'],
                                'nr_rates': movie['nr_rates'],
                                'url': movie["url"] if pd.notna(movie["url"]) else None
                            })

                    recommendation = {
                        'day_name': day_name,
                        'day_description': day_description,
                        'day_image': match['image'],
                        'movies': recommendation_movies,
                        'books': [{
                            'title': book['title'],
                            'description': match[f'match_book{i+1}_descr'],
                            'image': book['img_url'],
                            'rating': book['rating'],
                            'nr_rates': book['rating_count'],
                            'url': book['url'],
                        } for i, book in enumerate(books_list) if book is not None]
                    }
                    recommendations.append(recommendation)

    return render_template('home2.html', recommendations=recommendations)

if __name__ == "__main__":
    app.run(debug=True)


