<h1><b>Leisure Time</b></h1>
<img align="center" width="1000" alt="Header Image" src="https://raw.githubusercontent.com/jcosta92/LeisureTime/main/02 Readme/header.jpg" />

<details>
<summary><h2>1. Summary</h2></summary>

Aren’t you tired of choosing a random movie or book to see or watch? 
The objective of this project is to give you daily recommendations on movies and books, depending on the specific day in question. We have celebrities’ birthdays, international days and anniversaries of certain events, such as famous battles.
This project that originates *Leisure Time – Movie&Book Recommendation System* is based on an NLP model that was specifically searched for the purpose of connecting one description into another one.

</details>

<details>
<summary><h2>2. Python files</h2></summary>

- *Books.ipynb*
- *Days.ipynb*
- *model.ipynb*
- *Movies_IMDB.ipynb*
- *Movies_TMDP_API.ipynb*
- *appimdb.py*
- *appimdb2.py*
- *apptmdb.py*
- *apptmdb2.py*

</details>

<details>
<summary><h2>3. Datasets</h2></summary>

- "01 Queries" folder
- *df_birthdays_movies.csv*
- *df_birthdays_books.csv*
- *days.csv*
- *matches'%d%m%Y'_TMDB.csv*
- *matches'%d%m%Y'_IMDB.csv*
- *goodreads.csv*
- *best_books.csv*
- *TMDB_movies_final.csv*
- *imdb_movie_fetch.csv*

</details>

<details>
<summary><h2>4. Interface</h2></summary>


  
<img align="center" width="1000" alt="Header Image" src="https://raw.githubusercontent.com/jcosta92/LeisureTime/main/02 Readme/interface.jpg" />
</details>

<details>
<summary><h2>5. Books</h2></summary>

The python book used for dealing with the books dataframe was *Books.ipynb*.
The books dataframe used was from Kaggle, from the following source:
-	[*goodreads.csv*](https://www.kaggle.com/datasets/khushdassani/goodreads-300k-dataset?select=goodreads.csv)

The dataset was cleaned to Latin and English titles, using the langid library.
This dataframe was also reduced to the books with a certain minimum rating and votes. In this case, the final dataframe of books has only books with at least 3.5 rating and 1000 votes - *best_books.csv*.
In the end, we get the authors' birthdays by webscraping Wikipedia to add to our Days dataframe - *df_birthdays_books.csv*.

</details>

<details>
<summary><h2>6. Movies</h2></summary>

The focus of this project was the movies, because nowadays we give more focus into television. So there were 2 approaches to get movie data:

1.	From TMBD API – using the API from: [*https://www.themoviedb.org/*](https://www.themoviedb.org/)

2.	From IMDB website – using Web Scraping, from IMDB advanced search system
   Each of the processes takes more than 12 hours to run. Web Scraping can be time-consuming, especially when dealing with big data.

<details>
<summary><h3>6.1. TMDB API </h3></summary>

To use TMDB API in *Movies_TMDB_API.ipynb* the following steps were made to get the correct bearer and API key: [https://developer.themoviedb.org/reference/intro/getting-started/*](https://developer.themoviedb.org/reference/intro/getting-started/). To get more data, such as actors, budgets, revenues, imdb ids and streams the following source was used: [https://github.com/celiao/tmdbsimple/blob/master/README.md](https://github.com/celiao/tmdbsimple/blob/master/README.md). 
```python
base_url = "https://api.themoviedb.org/3/discover/movie"
headers = {
"accept": "application/json",
"Authorization": "Bearer YOUR_BEARER" ######### ------------------------- FROM TMDB API
}
```
```python
tmdb.API_KEY = 'YOUR_API_KEY' ######## ------------------- select from your TMDB API KEY
tmdb.REQUESTS_SESSION = requests.Session()
```
</details>




</details>



