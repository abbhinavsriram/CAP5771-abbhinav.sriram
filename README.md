# CAP 5771 Final Project - Abbhinav Sriram and Aelly Alwardi

## Investigating contrasting perspectives between developers and mainstream media on AI implementation concerns


### Installation requirements

Required Python version: 3.11

To install the required modules, run the command

```
pip install -r requirements.txt
```

All of our data is stored on the SQLite file "db.sqlite"

Developer Posts code files:
* get_dev_posts.ipynb is the code used to extract the developer posts about AI
* dev_data_exploration.ipynb is the code used to do basic data exploration of these articles (post times, key words used, word count)

News Articles code files:
* get_news_articles.py is the code used to get news articles from the infini-news-corpus dataset, combine all the news data into a SQL table, and view the frequency of articles per month

* combine_sqlite_dbs.py is the code used to combine the two SQLite databases into one. This was only needed during development. the current db.sqlite file should already include all the necessary data
