from requests import get
from json import dump, load
from bs4 import BeautifulSoup
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def get_articles():
    API_KEY = "GAtwkeGZptaol9lOzMTAgLA3JGDO9SoZXG91DYKAcolexad6"
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


def main():
    # get_articles()
    json_response = read_articles()
    for item in json_response:
        if item["section_name"] == "Technology":
            headline = item["headline"]["main"]
            snippet = item["snippet"]
            pub_date = item["pub_date"]
            print("-----------------")
            print("Headline: ", headline)
            print("Pub Date: ", pub_date)
            print("Snippet: ", snippet)
            # for k, v in item.items():
            #     print(k, v)
            print("-----------------")
            print()
        # break
        # print(item)

    # url = json_response[0]["web_url"]
    #
    # service = Service(executable_path="")
    # driver = webdriver.Chrome(service=service)
    # print(scrape_article(url, driver))

    # article = get(url)
    # soup = BeautifulSoup(article.text, "html.parser")
    # print(soup.prettify())




if __name__ == "__main__":
    main()