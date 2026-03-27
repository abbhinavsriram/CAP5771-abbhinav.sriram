# %%
import requests
import sqlite3
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH       = "dev_ai_articles_full.sqlite"  # same DB as dev.to
PER_PAGE      = 100
MAX_WORKERS   = 5
BATCH_SIZE    = 100

# ── GraphQL ───────────────────────────────────────────────────────────────────
QUERY = """
  query GetAIPosts($after: String) {
    tag(slug: "ai") {
      posts(first: 50, after: $after, filter: { sortBy: recent }) {
        pageInfo {
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            title
            url
            slug
            publishedAt
            content {
              markdown
            }
            tags {
              name
              slug
            }
          }
        }
      }
    }
  }
"""

# ── Reuse your existing markdown_to_text ─────────────────────────────────────
def markdown_to_text(markdown):
    markdown = re.sub(r"```[\s\S]*?```", " ", markdown)
    markdown = re.sub(r"`[^`]*`", " ", markdown)
    markdown = re.sub(r"!\[[^\]]*\]\([^\)]*\)", " ", markdown)
    markdown = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", markdown)
    markdown = re.sub(r"<[^>]+>", " ", markdown)
    markdown = re.sub(r"[#>*_~\-]+", " ", markdown)
    return " ".join(markdown.split())

# ── Schema ────────────────────────────────────────────────────────────────────
def ensure_hashnode_schema(connection):
    print("[DB] Creating hashnode_articles table if needed...")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS hashnode_articles (
            id TEXT PRIMARY KEY,
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

def upsert_hashnode_article(connection, article):
    connection.execute(
        """
        INSERT INTO hashnode_articles (id, title, url, published_at, tags, body_text)
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
            article["published_at"],
            article["tags"],
            article["body_text"],
        ),
    )
def fetch_hashnode_pages():
    after = None
    has_next_page = True
    page = 1

    while has_next_page:
        response = requests.post(
            "https://gql.hashnode.com",
            json={"query": QUERY, "variables": {"after": after}},
        )

        if response.status_code != 200:
            print(f"[ERROR] HTTP {response.status_code} on page {page}: {response.text}")
            print(f"[RETRY] Waiting 5s before retrying page {page}...")
            time.sleep(5)
            continue

        result = response.json()

        # Log errors but don't skip — these are partial errors, data is still usable
        if "errors" in result:
            for err in result["errors"]:
                print(f"[WARN] {err['message']} (path: {err.get('path')})")

        # Only break if data is truly missing — don't retry, it won't recover
        if not result.get("data") or not result["data"].get("tag"):
            print("[WARN] No data in response, stopping")
            break  # ← was continue, caused infinite loop

        posts = result["data"]["tag"]["posts"]
        nodes = [edge["node"] for edge in posts["edges"]]

        print(f"[PAGE {page}] fetched {len(nodes)} nodes | hasNextPage={posts['pageInfo']['hasNextPage']}")
        yield from nodes

        has_next_page = posts["pageInfo"]["hasNextPage"]
        after = posts["pageInfo"]["endCursor"]
        page += 1
        time.sleep(0.5)

# %%


# This is the list of keywords that we can use to determine if an article is relevant to our question
# Match with: any(kw in article_text.lower() for kw in KEYWORDS)
# Stems catch all morphological variants automatically.
# Used AI to help generate this list
KEYWORDS = [

    # --- Hallucination & Factual Reliability ---
    "hallucin",        # hallucination, hallucinating
    "factual",         # factuality, factually
    "verif",           # verify, verification, verifiable
    "accurac",         # accuracy, inaccuracy

    # --- Bias & Fairness ---
    "bias",            # bias, biased, debiasing, bias detection
    "fairness",
    "discriminat",     # discrimination, discriminatory
    "intersectional",

    # --- Safety & Responsible AI ---
    "ai safety",
    "responsible ai",
    "align",           # alignment, misaligned
    "guardrail",       # guardrails
    "red team",        # red teaming, red-teaming

    # --- Explainability & Transparency ---
    "explain",         # explainability, explainable, explanation
    "interpret",       # interpretable, interpretability
    "transparen",      # transparency, transparent
    "audit",           # auditability, auditable, auditing

    # --- Privacy & Data Risk ---
    "privac",          # privacy, privacy-preserving
    "pii",
    "data leak",       # data leakage, data leak
    "data retent",     # data retention
    "consent",

    # --- Security & Adversarial Attacks ---
    "prompt inject",   # prompt injection
    "jailbreak",       # jailbreak, jailbreaking
    "adversarial",

    # --- Misinformation & Synthetic Media ---
    "misinform",        # misinformation, misinformed
    "disinform",       # disinformation
    "wrong",
    "deepfake",        # deepfake, deepfakes
    "fake news",

    # --- Ethics & Governance ---
    "ethic",           # ethics, ethical, unethical
    "governance",
    "regulat",         # regulation, regulatory, regulating
    "complian",        # compliance, compliant
    "ai act",
    "polic",           # policy, policies

    # --- Agentic AI & Automation ---
    "agentic",
    "autonomous",      # autonomous, autonomously, autonomy
    "automat",         # automate, automation, automated
    "workflow",

    # --- Retrieval & Grounding ---
    "retriev",         # retrieval, retrieve, retriever
    "grounding",
    "context",

    # --- Observability & Reliability ---
    "observ",          # observability, observable
    "model drift",
    "monitor",         # monitoring, monitored

    # --- Environmental Impact ---
    "sustainab",       # sustainability, sustainable
    "carbon footprint",
    "energy consumpt", # energy consumption
    "green ai",

    # --- Workforce & Economic Impact ---
    "layoff",          # layoff, layoffs
    "job displac",     # job displacement
    "reskill",         # reskilling, reskilled
    "redundanc",       # redundancy, redundancies
    "unemploy",        # unemployment, unemployed
    
    # --- Copyright & IP ---
    "copyright",
    "licens",          # licensing, licensed, license
    "plagiar",         # plagiarism, plagiarize
    "training data",
    "original",        # originality, original work

    # --- Cost & Scalability ---
    "inference cost",
    "vendor lock",     # vendor lock-in
    "productiv",       # productivity, productive
    "augment",         # augmentation, augmented

    # --- Harmful Content ---
    "toxic",           # toxic, toxicity
    "harmful",

    # --- AGI & Existential Risk ---
    "artificial general intelligence",
    "human-in-the-loop",
    "human in the loop",
    
	# --- AI Tooling & Human-in-the-loop ---
	"human in the loop",
	"human-in-the-loop",
	"context manag",       # context management
	"session context",
	"llm",
	"coding assistant",
	"ai assistant",
	"prompt engineer",     # prompt engineering
	"token",               # token, tokens, tokenization
	"context window",      # already have this
	"context drift",
    
	# --- AI Reasoning Failures ---
	"wrong context",
	"lost context",
	"confabul",            # confabulation (alternative term for hallucination)
	"confident",           # "confident but wrong" pattern
]

import re

SHORT_EXACT = {"rag", "agi", "pii"}

def is_ai_related(title, body_text):
    text = f"{title} {body_text}".lower()
    
    matched = set()
    for keyword in KEYWORDS:
        if keyword in SHORT_EXACT:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                matched.add(keyword)
        elif keyword in text:
            matched.add(keyword)
    
    return len(matched) >= 3

# %%
def process_node(node):
    try:
        markdown = (node.get("content") or {}).get("markdown") or ""
        body_text = markdown_to_text(markdown)
        url = node.get("url") or f"https://hashnode.com/post/{node['slug']}"
        title = node["title"]

        # same keyword filter as dev.to pipeline
        if not is_ai_related(title, body_text):
            print(f"[SKIP] No relevant keywords found: {title}")
            return None

        return {
            "id":           node["id"],
            "title":        title,
            "url":          url,
            "published_at": node.get("publishedAt"),
            "tags":         json.dumps([t["slug"] for t in node.get("tags", [])]),
            "body_text":    body_text,
        }
    except Exception as e:
        print(f"[ERROR] Failed to process node {node.get('id')}: {e}")
        return None


# %%
# ── Main ──────────────────────────────────────────────────────────────────────
connection = sqlite3.connect(DB_PATH)
ensure_hashnode_schema(connection)

seen_ids   = set()
batch_nodes = []
total_saved = 0

def process_and_save(nodes):
    global total_saved
    batch_records = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_node, node): node["id"] for node in nodes}
        for future in as_completed(futures):
            record = future.result()
            if record:
                batch_records.append(record)
                total_saved += 1

    for rec in batch_records:
        upsert_hashnode_article(connection, rec)
    connection.commit()
    print(f"[DB] Batch committed ({total_saved} total saved)")

# Process and save as pages come in instead of collecting everything first
for node in fetch_hashnode_pages():
    if node["id"] in seen_ids:
        continue
    seen_ids.add(node["id"])
    batch_nodes.append(node)

    if len(batch_nodes) >= BATCH_SIZE:
        process_and_save(batch_nodes)
        batch_nodes = []

# Flush remaining
if batch_nodes:
    process_and_save(batch_nodes)

connection.close()
print(f"\nDone. Total hashnode articles saved: {total_saved}")


