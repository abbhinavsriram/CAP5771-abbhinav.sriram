from requests import get
from json import dump, load
from time import sleep
from pandas import read_json
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud

def get_articles_from_api():
    API_KEY = ""
    search_term = "AI"
    page_number = 1
    offset = 0
    hits = -1
    docs = []
    try:
        while hits == -1 or offset + 10 < hits:
            response = get(f"https://api.nytimes.com/svc/search/v2/articlesearch.json?q={search_term}&api-key={API_KEY}&page={page_number}").json()
            print(offset, hits, response)
            hits = response["response"]["metadata"]["hits"]
            offset = response["response"]["metadata"]["offset"]
            page_number += 1
            docs.extend(response["response"]["docs"])

            with open("articles_1.json", "w") as file:
                dump(docs, file)
            sleep(13)

    except Exception as e:
        print(e)

def read_articles():
    with open("articles.json", "r") as file:
        return load(file)


def scrape_article(url, driver=None):
    driver.get(url)
    sleep(10)
    article = driver.page_source
    print(article)
    return article


def visualize():
    df = read_json("articles.json")
    months_posts = []
    for i, row in df.iterrows():
        months_posts.append(row["pub_date"][:7])

    keywords = ""
    for i, row in df.query("section_name == 'Technology'").iterrows():
        for keyword in row["keywords"]:
            keywords += keyword["value"] + " "

    sns.histplot(months_posts)
    plt.title("Number of posts per month")
    plt.show()

    plt.xticks(rotation=90)
    plt.title("Number of posts per section")
    sns.histplot(df["section_name"])
    plt.show()

    wordcloud = WordCloud(width=1500, height=800, background_color='white').generate(keywords)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title("Keywords used in NYT Tech articles mentioning AI")
    plt.show()


def main():
    # get_articles_from_api()
    visualize()

if __name__ == "__main__":
    main()