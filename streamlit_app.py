"""Leisure Time - daily movie and book recommendations, as a Streamlit app.

Every day of the year already has matches pre-computed by the NLP model (model2.ipynb), so the page
shows new recommendations each day with no extra pipeline: it filters the matches by today's date.

    streamlit run streamlit_app.py
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"
IMDB_URL = "https://www.imdb.com/title/"

st.set_page_config(page_title="Leisure Time", page_icon="🎬", layout="wide")


@st.cache_data(show_spinner="Loading the catalogue...")
def load_data():
    matches = pd.concat([pd.read_csv("all_matches_part1.csv"), pd.read_csv("all_matches_part2.csv")],
                        ignore_index=True)
    books = pd.concat([pd.read_csv("best_books_part1.csv"), pd.read_csv("best_books_part2.csv")],
                      ignore_index=True)
    movies = pd.read_csv("TMDB_movies_final.csv")
    for df in (matches, books, movies):
        obj = df.select_dtypes(include=["object", "string"]).columns
        df[obj] = df[obj].replace("&apos;", "'", regex=True)
    matches["Date"] = matches["Date"].astype(str).str[:10]
    # one row per title, so a lookup by title is a dictionary access
    books = books.drop_duplicates("title").set_index("title")
    movies = movies.sort_values("vote_count", ascending=False).drop_duplicates("title").set_index("title")
    return matches, books, movies


def day_kind(row) -> str:
    if pd.notna(row["Country"]):
        return "International day"
    if row["description"] == "birthday":
        return "Birthday"
    return "Anniversary"


def day_title(row) -> tuple[str, str]:
    kind = day_kind(row)
    if kind == "International day":
        return f"{row['Name']} ({row['Country']})", str(row["description"])
    if kind == "Birthday":
        return f"{row['Name']}", f"Born on {row['Date']}"
    return f"{row['Name']} ({row['Date']})", str(row["description"]).strip()


def stars(rating, scale=10) -> str:
    return f"⭐ {rating:.1f}/{scale}" if pd.notna(rating) else ""


def show_movie(title: str, descr: str, movies: pd.DataFrame):
    m = movies.loc[title] if title in movies.index else None
    if m is not None and pd.notna(m.get("backdrop_path")):
        st.image(TMDB_IMAGE_URL + m["backdrop_path"], use_container_width=True)
    if m is not None and pd.notna(m.get("imdb_id")):
        st.markdown(f"**[{title}]({IMDB_URL}{m['imdb_id']})**")
    else:
        st.markdown(f"**{title}**")
    if m is not None:
        st.caption(f"{stars(m['vote_average'])} · {int(m['vote_count']):,} votes")
    st.write(descr if isinstance(descr, str) else "")


def show_book(title: str, descr: str, books: pd.DataFrame):
    b = books.loc[title] if title in books.index else None
    cols = st.columns([1, 3])
    with cols[0]:
        if b is not None and pd.notna(b.get("img_url")):
            st.image(b["img_url"], use_container_width=True)
    with cols[1]:
        if b is not None and pd.notna(b.get("url")):
            st.markdown(f"**[{title}]({b['url']})**")
        else:
            st.markdown(f"**{title}**")
        if b is not None:
            st.caption(f"{b['authorName']} · {stars(b['rating'], 5)} · {int(b['rating_count']):,} ratings")
        text = descr.strip() if isinstance(descr, str) else ""
        st.write(text[:400] + ("..." if len(text) > 400 else ""))


matches, books, movies = load_data()

st.title("🎬📚 Leisure Time")
st.write("Movie and book recommendations for today's international days, birthdays and anniversaries, "
         "matched by an NLP model (Universal Sentence Encoder).")

with st.sidebar:
    chosen = st.date_input("Day", value=date.today(), help="Defaults to today; pick any day of the year.")
    shuffle = st.button("🔀 Show other picks for this day")
    st.caption("Data: TMDB, Goodreads, UN/UNESCO observances, Wikipedia. "
               "[Source code](https://github.com/jcosta92/LeisureTime)")

today = matches[(matches["Month"] == chosen.month) & (matches["Day"] == chosen.day)]
if today.empty:
    st.info("No matches for this day.")
    st.stop()

# Stable picks for the day; the shuffle button draws new ones.
seed_key = f"seed-{chosen.isoformat()}"
if seed_key not in st.session_state or shuffle:
    st.session_state[seed_key] = int(pd.Timestamp.now().value % 1_000_000) if shuffle else chosen.toordinal()
seed = st.session_state[seed_key]

st.subheader(chosen.strftime("%A, %d %B"))
for kind in ["International day", "Birthday", "Anniversary"]:
    group = today[today.apply(day_kind, axis=1) == kind]
    if group.empty:
        continue
    row = group.sample(1, random_state=seed).iloc[0]
    name, description = day_title(row)
    st.divider()
    head = st.columns([1, 3])
    with head[0]:
        if isinstance(row["image"], str) and row["image"].startswith("http"):
            st.image(row["image"], use_container_width=True)
    with head[1]:
        st.caption(kind.upper())
        st.header(name)
        st.write(description[:500] + ("..." if len(description) > 500 else ""))

    picks_movies = [(row[f"match_movie{i}"], row[f"match_movie{i}_descr"]) for i in (1, 2, 3)
                    if isinstance(row[f"match_movie{i}"], str)]
    picks_books = [(row[f"match_book{i}"], row[f"match_book{i}_descr"]) for i in (1, 2, 3)
                   if isinstance(row[f"match_book{i}"], str)]
    if picks_movies:
        st.markdown("##### 🎬 Movies")
        for col, (t, d) in zip(st.columns(3), picks_movies):
            with col:
                show_movie(t, d, movies)
    if picks_books:
        st.markdown("##### 📚 Books")
        for col, (t, d) in zip(st.columns(3), picks_books):
            with col:
                show_book(t, d, books)
