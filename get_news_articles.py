from datetime import datetime, timedelta
from pandas import DataFrame, read_csv
from matplotlib import pyplot as plt
from huggingface_hub import login
from datasets import load_dataset
from os import remove, rename
from threading import Thread
from sqlite3 import connect
from os.path import isfile

try:
    from secrets import HF_TOKEN
except ImportError:
    if input("Would you like to login to Hugging Face Hub? (y/n) ").lower() == "y":
        HF_TOKEN = input("Enter your Hugging Face Access Token: ")
    else:
        HF_TOKEN = None


# Constants
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
YELLOW = "\033[33m"
PURPLE = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[0m"
COLORS = [RED, YELLOW, GREEN, CYAN, BLUE, PURPLE]

AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "large language model",
    " llm ",
    "generative AI",
    "a.i.",
    " ai "
]


REPUTABLE_SOURCES = [
    "associated press",
    "forbes",
    "business insider",
    "reuters",
    "politico",
    "the guardian",
    "cnbc",
    "cnn",
    "fox news",
    "the washington post",
    "the seattle times",
    "new york post",
    "abc news",
    "bloomberg",
]


# See if article meets the criteria
def verify_filters(text, date, source):
    if date is None or text is None or source is None:
        return False

    year = int(date[:4])
    text = text.lower()

    in_date_range = 2020 <= year <= 2025
    word_count = len(text.split(" ")) > 500
    ai_mentions = sum([text.count(keyword.lower()) for keyword in AI_KEYWORDS]) > 6
    unique_ai_mentions = sum([1 for keyword in AI_KEYWORDS if keyword in text]) > 3
    is_reputable = source.lower() in REPUTABLE_SOURCES

    return in_date_range and word_count and (ai_mentions or unique_ai_mentions) and is_reputable


def get_articles_from_year(year, num_needed):
    color = COLORS[int(year) % 6]
    articles = []
    used_articles = []
    avg_time = 1

    # Load streaming dataset
    if HF_TOKEN:
        login(HF_TOKEN)

    dataset = load_dataset(
        "ruggsea/infini-news-corpus",
        data_files=f"data/year={year}/*.parquet",
        split="train",
        streaming=True
    )

    save_file = f"news_data/ai_articles_{year}.csv"
    start_time = datetime.now()
    for article in dataset:
        if len(articles) >= num_needed:
            break

        text = article.get("text", "")
        date = article.get("date", None)
        source = article.get("sitename", None)
        url = article.get("url", None)
        title = article.get("title", "")
        hashed = text[:50]

        if verify_filters(text, date, source) and hashed not in used_articles:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            avg_time = (avg_time * len(articles) + duration) / (len(articles) + 1)
            start_time = end_time
            eta = timedelta(seconds=avg_time * (num_needed - len(articles))) + end_time
            print(f"{color}{end_time.strftime('%m/%d %I:%M%p')} {len(articles)} {year} articles. ETA: {eta.strftime('%m/%d %I:%M%p')}{WHITE}")

            articles.append({
                "url": url,
                "date": date,
                "title": title,
                "text": text,
                "sitename": source
            })
            used_articles.append(hashed)

            # Occasional save state
            if len(articles) % 20 == 0 and len(articles) > 0:
                df = DataFrame(articles)
                if isfile(save_file):
                    rename(save_file, "temp.csv")
                df.to_csv(save_file, index=False)
                if isfile("temp.csv"):
                    remove("temp.csv")

    df = DataFrame(articles)
    print(f"Collected {len(articles)} articles")
    if isfile(save_file):
        rename(save_file, "temp.csv")
    df.to_csv(save_file, index=False)
    if isfile("temp.csv"):
        remove("temp.csv")

    return articles


# Get articles from dataset
def download_articles(max_articles=1500):
    print(f"Downloading articles {max_articles}")

    threads = []
    years = ["2025", "2024", "2023", "2022", "2021"]
    num_needed = max_articles // len(years)
    for year in years:
        thread = Thread(target=get_articles_from_year, args=(year, num_needed + len(years)))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def coalesce_articles():
    years = ["2025", "2024", "2023", "2022", "2021"]

    with open("news_data/ai_articles.csv", "w", encoding="utf-8") as csvfile:
        csvfile.write("url,date,title,text,source\n")

        for year in years:
            with open(f"news_data/ai_articles_{year}.csv", "r", encoding="utf-8") as year_file:
                lines = year_file.readlines()[1:]
            csvfile.write("".join(lines))

    # Convert to SQL database
    df = read_csv("news_data/ai_articles.csv")
    con = connect("db.sqlite")
    df.to_sql("NewsArticles", con=con, if_exists="replace")


def examine_date_freq():
    conn = connect("db.sqlite")
    cur = conn.cursor()
    cur.execute("select date from Articles")
    dates = cur.fetchall()
    month_counts = {}

    for date in dates:
        month = date[0][:7]
        month_counts[month] = month_counts.get(month, 0) + 1
    plt.xticks(rotation=90)
    month_counts = sorted(month_counts.items(), key=lambda x: x[0])
    months = [month[0] for month in month_counts]
    counts = [month[1] for month in month_counts]

    plt.bar(months, counts)
    plt.show()


if __name__ == "__main__":
    download_articles()
    coalesce_articles()
    examine_date_freq()
    print("Done")
