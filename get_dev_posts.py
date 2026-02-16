import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from dotenv import load_dotenv
import os
load_dotenv()
BASE_URL = "https://dev.to/api"
DEV_API_KEY = os.getenv("DEV_API_KEY")

# Headers for accessing API
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "abbhinav sriram",
    "api-key": DEV_API_KEY,

}

# the first filter, excluding popular tags that were most likely not associated with AI related articles
EXCLUDE_TAGS = {
    "php",
    "csharp",
    "angular",
    "ruby",
    "cryptocurrency",
    "bitcoin",
    "docker",
    "go",
    "codenewbie",
    "microservices",
    "flutter",
    "laravel",
    "kubernetes",
    "node",
    "tutorial",
}

# This is the batched API call to get articles
# it returns a list of article IDs which we can then make individual API calls to get the article details
def fetch_articles(page=1, per_page=10, tag=None, username=None, headers=None):
    params = {
        "page": page,
        "per_page": per_page,
        "tags_exclude": ",".join(sorted(EXCLUDE_TAGS)),
    }

    url = f"{BASE_URL}/articles?{urlencode(params)}"
    request_headers = dict(DEFAULT_HEADERS)
    if headers:
        request_headers.update(headers)

    request = Request(url, headers=request_headers)

    try:
        with urlopen(request) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"DEV API error {exc.code}: {detail}") from exc
    



import re
import time

# This is the individual API call to get article details by specific article ID
def fetch_article_by_id(article_id, headers=None, retries=3):
    url = f"{BASE_URL}/articles/{article_id}"
    request_headers = dict(DEFAULT_HEADERS)
    if headers:
        request_headers.update(headers)

    for attempt in range(retries):
        try:
            request = Request(url, headers=request_headers)
            print(f"[FETCH] Attempt {attempt + 1}/{retries} for article {article_id}")
            with urlopen(request) as response:
                payload = response.read().decode("utf-8")
                return json.loads(payload)
        except HTTPError as exc:
            if exc.code == 404:
                print(f"[FETCH] Article {article_id} not found (404), skipping")
                return None
            if exc.code == 429:
                print(f"[FETCH] Rate limited (429), waiting 5s before retry...")
                time.sleep(5)
                continue
            detail = exc.read().decode("utf-8")
            print(f"[FETCH] HTTP error {exc.code}: {detail}")
            if attempt == retries - 1:
                return None
            time.sleep(1)
        except Exception as e:
            print(f"[FETCH] Error on attempt {attempt + 1}: {e}")
            if attempt == retries - 1:
                return None
            time.sleep(1)
    
    return None

# Since each of the articles are written in .md, need to convert to plaintext for future NLP processing
def markdown_to_text(markdown):
    # Remove code blocks and inline code
    markdown = re.sub(r"```[\s\S]*?```", " ", markdown)
    markdown = re.sub(r"`[^`]*`", " ", markdown)

    # Remove images and links but keep link text
    markdown = re.sub(r"!\[[^\]]*\]\([^\)]*\)", " ", markdown)
    markdown = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", markdown)

    # Remove HTML tags
    markdown = re.sub(r"<[^>]+>", " ", markdown)

    # Strip markdown formatting characters
    markdown = re.sub(r"[#>*_~\-]+", " ", markdown)

    # Normalize whitespace
    return " ".join(markdown.split())



import sqlite3
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_PATH = "dev_notebooks/dev_ai_articles_full.sqlite"
TAGS = ["ai"]  # Fetch all articles; server-side tags_exclude handles tag filtering.
PER_PAGE = 500
DAYS_BACK = 2300
MAX_WORKERS = 5
BATCH_SIZE = 100


# This is the list of keywords that we can use to determine if an article is relevant to our question
KEYWORDS = [
    "hallucination",
    "hallucinations",
    "context window",
    "context length",
    "context limit",
    "context issues",
    "token limit",
    "long context",
    "prompt injection",
    "grounding",
    "retrieval",
    "rag",
    "automation",
    "automate",
    "agent",
    "autonomous",
    "workflow automation",
    "environmental impact",
    "carbon footprint",
    "energy usage",
    "energy consumption",
    "sustainability",
    "green ai",
    "layoff",
    "layoffs",
    "downsizing",
    "redundancy",
    "reduction in force",
    "rif",
    "bias",
    "fairness",
    "discrimination",
    "toxic",
    "harmful",
    "privacy",
    "data leakage",
    "pii",
    "data retention",
    "jailbreak",
    "jailbreaking",
    "accuracy",
    "factuality",
    "verification",
    "guardrails",
    "alignment",
    "safety",
    "copyright",
    "licensing",
    "layoffs",
    "layoff",
    "plagiarism",
    "training data",
    "regulation",
    "policy",
    "compliance",
    "governance",
    "ai act",
    "job displacement",
    "reskilling",
    "productivity",
    "augmentation",
    "inference cost",
    "compute",
    "pricing",
    "vendor lock-in",
    "lock-in",
    "deepfake",
    "deepfakes",
    "misinformation",
    "disinformation",
    "fake news",
    "ethic",
    "ethics",
    "water",
    "unemployment",
    "consent",
    "mistakes",
    "agi",
    "artificial general intelligence",
    "originality",
    "cut",
    "cuts"
]

# this is the function used to determine if the article is relevant using the keywords
# need 3 distinct keywords
def is_ai_related(title, body_text):
    text = f"{title} {body_text}".lower()
    matched = {keyword for keyword in KEYWORDS if keyword in text}
    return len(matched) >= 3



# parsing dates
def parse_iso8601(value):
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None

# create schema if not exists
def ensure_schema(connection):
    print("[DB] Creating schema if needed...")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            published_at TEXT,
            tags TEXT,
            body_text TEXT
        )
        """
    )
    connection.commit()
    print("[DB] Schema ready")

# add developer post to database
def upsert_article(connection, article):
    connection.execute(
        """
        INSERT INTO articles (id, title, url, published_at, tags, body_text)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            url=excluded.url,
            published_at=excluded.published_at,
            tags=excluded.tags,
            body_text=excluded.body_text
        """,
        (
            article["id"],
            article["title"],
            article["url"],
            article.get("published_at"),
            article.get("tags"),
            article.get("body_text")
        ),
    )




# gets articles for a given tag, going through the API's articles until we reach our cutoff date
def fetch_tagged_articles(tag, cutoff):
    page = 1
    article_count = 0
    tag_label = tag if tag else "(all)"
    while True:
        try:
            batch = fetch_articles(page=page, per_page=PER_PAGE, tag=tag)
        except Exception as e:
            break
            
        if not batch:
            break

        published_dates = [parse_iso8601(item.get("published_at")) for item in batch]
        published_dates = [dt for dt in published_dates if dt]
        if published_dates:
            oldest = min(published_dates)
            newest = max(published_dates)

        for item in batch:
            published = parse_iso8601(item.get("published_at"))
            if published and published < cutoff:
                return
            yield item
            article_count += 1

        page += 1
        # Sleep briefly to respect API rate limits and avoid overwhelming the server
        time.sleep(0.2)

def fetch_and_process_article(article_id):
	# get article body
    try:
        detail = fetch_article_by_id(article_id)
    except Exception as e:
        print(f"Failed to fetch article {article_id}: {e}")

        return None
    
    if detail is None:
        print(f"Skipping article {article_id} due to fetch failure")

        return None
        
    body_markdown = detail.get("body_markdown", "")
    body_text = markdown_to_text(body_markdown)
    title = detail.get("title", "")

    if not is_ai_related(title, body_text):
        print(f"Excluding article {article_id} since no relevant keywords found)")
        return None
    
    record = {
        "id": article_id,
        "title": title,
        "url": detail.get("url", ""),
        "published_at": detail.get("published_at"),
        "tags": ",".join(detail.get("tag_list", [])),
        "body_text": body_text
    }
    return record

# Effectively our main function

# As I mentioned, the dates go back to 2017, so I set a maximum limit for 2300 days back to accurately
# get a picture of AI discussions from before ChatGPT to today.

cutoff_date = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
print(f"Cutoff date: {cutoff_date}")

connection = sqlite3.connect(DB_PATH)
ensure_schema(connection)

seen_ids = set()
total_fetched = 0
total_saved = 0

for tag in TAGS:
    print(f"\n Starting tag: {tag if tag else '(all)'}")
    articles_to_fetch = []
    
    # Collect article IDs first
	# Good thing that the API had ID for articles, so I don't have to create my own key
    for item in fetch_tagged_articles(tag, cutoff_date):
        article_id = item["id"]
        if article_id in seen_ids:
            print(f"Skipping duplicate article {article_id}")
            continue
        seen_ids.add(article_id)
        articles_to_fetch.append(article_id)
        total_fetched += 1
    
    # Fetch all articles concurrently
    print(f"Fetching {len(articles_to_fetch)} articles with {MAX_WORKERS} threads...")
    batch_records = []
    
	# used threading since fetching article details is the bottleneck, and we can do it in parallel to speed up the process
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_and_process_article, aid): aid for aid in articles_to_fetch}
        
        for future in as_completed(futures):
            record = future.result()
            if record:
                batch_records.append(record)
                total_saved += 1
                
                # Also used batch inserts to speed up database writes (don't want to hit the database for every single article)
                if len(batch_records) >= BATCH_SIZE:
                    for rec in batch_records:
                        upsert_article(connection, rec)
                    connection.commit()
                    print(f"Batch committed ({total_saved} total articles saved)")
                    batch_records = []
    
    # Insert remaining records
    if batch_records:
        for rec in batch_records:
            upsert_article(connection, rec)
        connection.commit()
        print(f"Final batch committed ({total_saved} total articles saved)")

connection.close()

print(
    f"\nComplete. Fetched: {total_fetched}, Saved: {total_saved}, "
)



