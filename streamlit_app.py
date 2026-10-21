"""Leisure Time - daily movie and book recommendations, as a Streamlit app.

Every day of the year already has matches pre-computed by the NLP model (model2.ipynb), so the page
shows new recommendations each day with no extra pipeline: it filters the matches by today's date.

    streamlit run streamlit_app.py
"""
from __future__ import annotations

import re
from datetime import date

import pandas as pd
import requests
import streamlit as st

TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
IMDB_URL = "https://www.imdb.com/title/"
# Wikimedia asks for an identifying User-Agent and blocks anonymous or hotlinked requests.
HEADERS = {"User-Agent": "LeisureTime/1.0 (https://github.com/jcosta92/LeisureTime)"}
WIKI_FILEPATH = re.compile(r"(commons\.wikimedia\.org|en\.wikipedia\.org)/wiki/Special:FilePath/([^?#]+)")
WIKI_UPLOAD = re.compile(r"upload\.wikimedia\.org/wikipedia/(commons|en)/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/?#]+)")

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


def image_url(url: str, width: int = 400) -> str:
    """Rewrite Wikimedia links (full-size files, old thumbnail sizes, links starting with //) to a
    thumbnail of the given width, which Wikimedia serves; other links are returned unchanged."""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    m = WIKI_FILEPATH.search(url)
    if m:
        host, name = m.groups()
    else:
        m = WIKI_UPLOAD.search(url)
        if not m:
            return url
        site, name = m.groups()
        host = "commons.wikimedia.org" if site == "commons" else "en.wikipedia.org"
    return f"https://{host}/wiki/Special:FilePath/{name}?width={width}"


@st.cache_data(ttl=24 * 3600, max_entries=3000, show_spinner=False)
def _download(url: str) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=10)
    if not r.ok or not r.headers.get("content-type", "").startswith("image/"):
        raise ValueError(f"{r.status_code} for {url}")       # exceptions are not cached: retried later
    return r.content


def show_image(url) -> None:
    """Download the image on the server and serve it from the app itself, so browser blockers and
    hotlink protection can't break it. A failed image is skipped instead of shown as broken."""
    if not isinstance(url, str) or not url.strip():
        return
    try:
        st.image(_download(image_url(url)), use_container_width=True)
    except Exception:
        pass


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
        show_image(TMDB_IMAGE_URL + m["backdrop_path"])
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
            show_image(b["img_url"])
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
        show_image(row["image"])
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
