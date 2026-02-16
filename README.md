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

We initially wrote the DEV API extraction and exploration code in two separate Jupyter notebooks (stored in the /dev_notebooks folder). However, to keep in line with assignment specifications, we transferred the code to two separate .py files (though we recommend looking at the ipynb files since they contain the outputs)
* /dev_notebooks
  * get_dev_posts.ipynb is the code used to extract the developer posts about AI
  * dev_data_exploration.ipynb is the code used to do basic data exploration of these articles (post times, key words used, word count)
  * dev_ai_articles_full.sqlite is the file I initially stored the DEV API articles on (since Aelly and I were working on independent datasets, we didn't want to have a potential overwriting issue, so we maintained independent databases and combined them into db.sqlite later). Leaving this here for documentation purposes and so that the code can work during testing
* py files (for assignment specification)
  * get_dev_posts.py
  * dev_data_exploration.py

News Articles code files:
