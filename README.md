# CAP 5771 Final Project - Abbhinav Sriram and Aelly Alwardi

## Investigating contrasting perspectives between developers and mainstream media on AI implementation concerns

**Live app available at: data.aellyalwardi.com**


### Installation requirements

Required Python version: 3.11

To install the required modules, run the command

```
pip install -r requirements.txt
```

All of our data is stored in the SQLite file **db.sqlite**. This file isn't including in the repo since it is too large, instead you can generate it yourself by running the code in `generate_db.py`.


### Data pipeline code files
**Developer Posts code files:**

We initially wrote the DEV API extraction and exploration code in two separate Jupyter notebooks (stored in the /dev_notebooks folder). However, to keep in line with assignment specifications, we transferred the code to two separate .py files (though we recommend looking at the ipynb files since they contain outputs and extra notes)

* /dev_notebooks
  * get_dev_posts.ipynb is the code used to extract DEV.TO postys
  * get_hashnode_articles.ipynb: Code to extract developer posts from Hashnode
  * dev_data_exploration.ipynb is the code used to do basic data exploration of DEV.TO articles (post times, key words used, word count)
  * hashnode_data_exploration.ipynb is the same as above but for hashnode data extraction


**News Articles code files:** 
* get_news_articles.py is the code used to get news articles from the infini-news-corpus dataset, combine all the news data into a SQL table, and view the frequency of articles per month

* combine_sqlite_dbs.py is the code used to combine the two SQLite databases into one. This was only needed during development. the current db.sqlite file should already include all the necessary data


### Clustering and sentiment analysis notebooks
**clustering**

```
* /dev_notebooks
  * clustering.ipynb: Main clustering and classification pipeline for developer articles
  * news_clustering.ipynb: Same as above but for news articles

```
**Sentiment Analysis**

```
* /dev_notebooks
  * sentiment_analysis.ipynb: Sentiment Analysis for developer articles
  * news_sentiment_analysis: Same as above but for news
```
(The other files are kept to show our full process, but they are mainly experimental)


### Web app

```
* /webbapp
  * /backend
    * backend.py: Flask app
    * charting_functions.py: Backend for visualizations 1-4
    * similarity_search.py: Backend for similarity search functionality
  * /frontend
    * visualization_1-5.html: HTML frontend
  * similarity_search.js: JavaScript logic that receives python output and turns into frontend element
  * app.js: Same function as above but for visualizations 1-4
  * index.html: Home screen
```


### Running our Pipeline files


All the data has already been acquired and is in the repo. Since running the data acquisition code takes multiple days, we advise you to run `combine_sqlite_dbs`, which will automatically generate the `db.sqlite` file

To run our developer and news posts data, run the following files (processing time > 3 days due to rate limits)
```
dev_notebooks/
  get_hashnode_articles.ipynb
  get_dev_posts.ipynb

get_news_articles.py

```
Then, to run our data clustering notebooks, run

```
dev_notebooks/
  clustering.ipynb
  news_clustering.ipynb
```
To run our data sentiment analysis notebooks, run

```
dev_notebooks/
  dev_sentiment.ipynb
  news_sentiment_analysis.ipynb
```

### Running the Flask applications

Run 
```
python webbapp/backend/backend.py
```
in the root directory to start the flask application.


Alternatively, you can navigate to data.aellyalwardi.com to use the tool live