from huggingface_hub import login
from datasets import load_dataset
from os import remove, rename
from pandas import DataFrame
from sqlite3 import connect
from secrets import HF_TOKEN

# Constants
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
    ai_mentions = sum([text.count(keyword.lower()) for keyword in AI_KEYWORDS]) > 3
    is_reputable = source.lower() in REPUTABLE_SOURCES

    return in_date_range and word_count and  ai_mentions and is_reputable


# Get articles from dataset
def download_articles():
    # Load streaming dataset
    login(HF_TOKEN)
    dataset = load_dataset(
        "ruggsea/infini-news-corpus",
        split="train",
        streaming=True
    )

    articles = []
    used_articles = []
    max_articles = 1500
    valid_articles = 0
    years = {}

    for article in dataset:
        if valid_articles >= max_articles:
            break

        text = article.get("text", "")
        date = article.get("date", None)
        source = article.get("sitename", None)
        url = article.get("url", None)
        title = article.get("title", "")
        hashed = (source, title)
        year = date[:4]

        if verify_filters(text, date, source) and hashed not in used_articles:

            articles.append({
                "url": url,
                "date": date,
                "title": title,
                "text": text,
                "sitename": source
            })
            used_articles.append(hashed)

            # Make sure there's a diverse date range
            years[year] = years.get(year, 0) + 1
            if years[year] < 320:
                valid_articles += 1

            # Occasional save state
            if valid_articles % 100 == 0 and valid_articles > 0:
                print(f"Collected {len(articles)} articles")

                df = DataFrame(articles)
                rename("ai_articles_2020_2025.csv", "temp.csv")
                df.to_csv("ai_articles_2020_2025.csv", index=False)
                remove("temp.csv")

    print(f"Collected {len(articles)} articles")
    df = DataFrame(articles)
    rename("ai_articles_2020_2025.csv", "temp.csv")
    df.to_csv("ai_articles_2020_2025.csv", index=False)
    remove("temp.csv")

    # Convert to SQL database
    con = connect("articles.db")
    df.to_sql("articles", con=con, if_exists="replace")


if __name__ == "__main__":
    download_articles()
