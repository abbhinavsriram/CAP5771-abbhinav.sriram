# CAP 5771 Final Project - Abbhinav Sriram and Aelly Alwardi

## Investigating contrasting perspectives between developers and mainstream media on AI implementation concerns


### Installation requirements

Required Python version: 3.11

To install the required modules, run the command

```
pip install -r requirements.txt
```

All of our data is stored in the SQLite file **db.sqlite**. This file isn't including in the repo since it is too large, instead you can generate it yourself by running the code in `generate_db.py`.

**Developer Posts code files:**

We initially wrote the DEV API extraction and exploration code in two separate Jupyter notebooks (stored in the /dev_notebooks folder). However, to keep in line with assignment specifications, we transferred the code to two separate .py files (though we recommend looking at the ipynb files since they contain outputs and extra notes)

* /dev_notebooks
  * get_dev_posts.ipynb is the code used to extract the developer posts about AI
  * dev_data_exploration.ipynb is the code used to do basic data exploration of these articles (post times, key words used, word count)
  * dev_ai_articles_full.sqlite is the file I initially stored the DEV API articles on (since Aelly and I were working on independent datasets, we didn't want to have a potential overwriting issue, so we maintained independent databases and combined them into db.sqlite later). Leaving this here for documentation purposes and so that the code can work during testing
* py files (for assignment specification)
  * get_dev_posts.py
  * dev_data_exploration.py

News Articles code files:
* get_news_articles.py is the code used to get news articles from the infini-news-corpus dataset, combine all the news data into a SQL table, and view the frequency of articles per month

* combine_sqlite_dbs.py is the code used to combine the two SQLite databases into one. This was only needed during development. the current db.sqlite file should already include all the necessary data

### Running Files
All the data has already been acquired and is in the repo. Since running the data acquisition code takes multiple days, we advise you to run `combine_sqlite_dbs`, which will automatically generate the `db.sqlite` file

To run our developer posts data acquisition file, run
```
python get_dev_posts.py
```
in the root directory


To run our news articles data acquisition file, run
```
python get_news_articles.py
```
in the root directory
