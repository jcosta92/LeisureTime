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

matches_part1 = pd.read_csv("all_matches_part1.csv")
matches_part2 = pd.read_csv("all_matches_part2.csv")

matches = pd.concat([matches_part1, matches_part2], ignore_index=True).reset_index(drop=True)

#filter today
matches = matches[(matches["Month"] == today.month) & (matches["Day"] == today.day)]
# matches=pd.read_csv("matches29072023_IMDB.csv") # --- use if you want a specific csv

# Concatenating books parts
books_part1 = pd.read_csv("best_books_part1.csv")
books_part2 = pd.read_csv("best_books_part2.csv")

books = pd.concat([books_part1, books_part2], ignore_index=True).reset_index(drop=True)

movies = pd.read_csv("imdb_movie_fetch.csv")

# Replace &apos; with '
matches = matches.replace("&apos;", "'", regex=True)
books = books.replace("&apos;", "'", regex=True)
movies = movies.replace("&apos;", "'", regex=True)

matches["Date"] = matches["Date"].str[:10]

openai.api_key = "YOUR_API_KEY" ##### -------- input your OpenAI API key

def truncate_recommendation(recommendation):
    # Find the last occurrence of period (.), comma (,), or exclamation mark (!) in the recommendation text
    last_period_index = recommendation.rfind(".")
    last_exclamation_index = recommendation.rfind("!")
    
    # Get the maximum index among period, comma, and exclamation mark
    last_index = max(last_period_index, last_exclamation_index)
    
    if last_index != -1:
        # Truncate the text at the last index
        recommendation = recommendation[:last_index+1]
    
    # Return the truncated recommendation
    return recommendation


def generate_snack_recommendation(movie_title, movie_description):
    # Generate the prompt for the OpenAI API for snack recommendation
    prompt = f"Movie Title: {movie_title}\nMovie Description: {movie_description}\nRecommend me a snack based on the movie title and description. (If you recommend popcorn, please also recommend a second snack. You can recommend popcorn, but not always)"

    # Generate snack recommendation using OpenAI's completion API
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=25,
        temperature=0.5,
        n=1,
        stop=None
    )

    # Extract the recommended snack from the API response
    snack_recommendation = response.choices[0].text.strip()
    
    # Truncate the snack recommendation
    snack_recommendation = truncate_recommendation(snack_recommendation)

    # Return the snack recommendation
    return snack_recommendation


def generate_drink_recommendation(movie_title, movie_description):
    # Generate the prompt for the OpenAI API for drink recommendation
    prompt = f"Movie Title: {movie_title}\nMovie Description: {movie_description}\nRecommend me a drink based on the movie title and description."

    # Generate drink recommendation using OpenAI's completion API
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=prompt,
        max_tokens=25,
        temperature=0.5,
        n=1,
        stop=None
    )

    # Extract the recommended drink from the API response
    drink_recommendation = response.choices[0].text.strip()
    
    # Truncate the drink recommendation
    drink_recommendation = truncate_recommendation(drink_recommendation)

    # Return the drink recommendation
    return drink_recommendation

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
                            snack_recommendation = generate_snack_recommendation(movie['title'], match[f'match_movie{i+1}_descr'])
                            drink_recommendation = generate_drink_recommendation(movie['title'], match[f'match_movie{i+1}_descr'])
                            recommendation_movies.append({
                                'title': movie['title'],
                                'description': match[f'match_movie{i+1}_descr'],
                                'image': movie["image"] if pd.notna(movie["image"]) else None,
                                'rating': movie['rating'],
                                'nr_rates': movie['nr_rates'],
                                'url': movie["url"] if pd.notna(movie["url"]) else None,
                                'snack_recommendation': snack_recommendation,
                                'drink_recommendation': drink_recommendation
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

    return render_template('home.html', recommendations=recommendations)

if __name__ == "__main__":
    app.run(debug=True)


