import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit.components.v1 import html

today = datetime.today()
matches_part1 = pd.read_csv("all_matches_part1.csv")
matches_part2 = pd.read_csv("all_matches_part2.csv")

matches = pd.concat([matches_part1, matches_part2], ignore_index=True).reset_index(drop=True)

books = pd.read_csv("best_books.csv")
movies = pd.read_csv("TMDB_movies_final.csv")

# Replace &apos; with '
matches = matches.replace("&apos;", "'", regex=True)
books = books.replace("&apos;", "'", regex=True)
movies = movies.replace("&apos;", "'", regex=True)

TMDB_BASE_URL = "https://www.imdb.com/title/"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/original"

matches["Date"] = matches["Date"].str[:10]

# Streamlit App
def main():
    st.title("Leisure Time Recommendations")

    international_days = matches[matches['Country'].notna()]
    birthdays = matches[matches['description'] == "birthday"]
    anniversaries = matches[(matches['Country'].isna()) & (matches['description'] != "birthday")]

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
                                'image': TMDB_IMAGE_URL + movie['backdrop_path'] if pd.notna(movie['backdrop_path']) else None,
                                'rating': movie['vote_average'],
                                'nr_rates': movie['vote_count'],
                                'url': TMDB_BASE_URL + str(movie['imdb_id']) if pd.notna(movie['imdb_id']) else None
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

    # Display the HTML template using streamlit.components.v1.html
    html_template = "home2.html"
    with open(html_template, "r") as f:
        template = f.read()
        rendered_template = template.format(recommendations=recommendations)
        st.components.v1.html(rendered_template, height=1000)

if __name__ == "__main__":
    main()
