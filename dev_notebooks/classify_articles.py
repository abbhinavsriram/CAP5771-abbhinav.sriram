"""
AI Article Classifier Pipeline
================================
Classifies 25k AI-tagged articles into TECHNICAL vs NON-TECHNICAL,
then sub-tags non-technical ones (environment, legal, ethics, etc.)

Requirements:
    pip install sentence-transformers scikit-learn hdbscan transformers torch pandas tqdm psycopg2-binary

Usage:
    1. Configure DB_CONFIG and COLUMN_CONFIG below
    2. Run: python classify_articles.py
    3. Results are written back to a new table in your database
"""

import sqlite3
import pandas as pd
import numpy as np
from tqdm import tqdm
import json

# ─────────────────────────────────────────────
# CONFIGURATION — edit these
# ─────────────────────────────────────────────

# Set DB_TYPE to "sqlite" or "postgres"
DB_TYPE = "sqlite"

SQLITE_PATH = "articles.db"  # path to your .db file

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "your_db",
    "user": "your_user",
    "password": "your_password",
}

# Your table and column names
TABLE_NAME = "articles"
COLUMN_CONFIG = {
    "id": "id",           # primary key column
    "title": "title",     # article title column
    "body": "body",       # article body/content column (set to None if not available)
}

# Output table where results will be written
OUTPUT_TABLE = "article_classifications"

# How much body text to use (tokens are expensive; first 500 chars is usually enough)
BODY_PREVIEW_CHARS = 500

# Batch size for zero-shot classification (lower if you run out of RAM)
CLASSIFICATION_BATCH_SIZE = 32

# ─────────────────────────────────────────────
# STEP 1: Load articles from DB
# ─────────────────────────────────────────────

def get_connection():
    if DB_TYPE == "sqlite":
        return sqlite3.connect(SQLITE_PATH)
    elif DB_TYPE == "postgres":
        import psycopg2
        return psycopg2.connect(**POSTGRES_CONFIG)
    else:
        raise ValueError("DB_TYPE must be 'sqlite' or 'postgres'")


def load_articles():
    print("📦 Loading articles from database...")
    conn = get_connection()
    
    id_col = COLUMN_CONFIG["id"]
    title_col = COLUMN_CONFIG["title"]
    body_col = COLUMN_CONFIG["body"]
    
    if body_col:
        query = f"SELECT {id_col}, {title_col}, {body_col} FROM {TABLE_NAME}"
    else:
        query = f"SELECT {id_col}, {title_col} FROM {TABLE_NAME}"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Build a single text field to embed/classify
    if body_col and body_col in df.columns:
        df["text"] = (
            df[title_col].fillna("") + " " +
            df[body_col].fillna("").str[:BODY_PREVIEW_CHARS]
        ).str.strip()
    else:
        df["text"] = df[title_col].fillna("")
    
    print(f"✅ Loaded {len(df):,} articles")
    return df


# ─────────────────────────────────────────────
# STEP 2: Embed articles
# ─────────────────────────────────────────────

def embed_articles(df):
    print("\n🔢 Generating embeddings (this takes a few minutes on first run)...")
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer("all-MiniLM-L6-v2")  # ~80MB, fast, good quality
    
    texts = df["text"].tolist()
    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    print(f"✅ Embeddings shape: {embeddings.shape}")
    return embeddings


# ─────────────────────────────────────────────
# STEP 3: Cluster to find natural groups
# ─────────────────────────────────────────────

def cluster_articles(embeddings, n_clusters=20):
    print(f"\n🗂️  Clustering into {n_clusters} groups...")
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.decomposition import PCA
    
    # Reduce dims first for speed
    print("   Reducing dimensions with PCA...")
    pca = PCA(n_components=50, random_state=42)
    reduced = pca.fit_transform(embeddings)
    
    print("   Running k-means...")
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    labels = km.fit_predict(reduced)
    
    print(f"✅ Clustering done. Cluster sizes:")
    unique, counts = np.unique(labels, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"   Cluster {u:2d}: {c:,} articles")
    
    return labels


def sample_clusters(df, cluster_labels, n_samples=5):
    """Print sample article titles per cluster for manual inspection."""
    print("\n📋 Sample articles per cluster (for your reference):")
    df = df.copy()
    df["cluster"] = cluster_labels
    for cluster_id in sorted(df["cluster"].unique()):
        samples = df[df["cluster"] == cluster_id]["text"].head(n_samples).tolist()
        print(f"\n  ── Cluster {cluster_id} ──")
        for s in samples:
            print(f"    • {s[:120]}")


# ─────────────────────────────────────────────
# STEP 4: Zero-shot classification
# ─────────────────────────────────────────────

CANDIDATE_LABELS_PRIMARY = [
    "technical AI discussion about code, models, or implementation",
    "non-technical discussion about AI society, ethics, law, or environment",
]

CANDIDATE_LABELS_SECONDARY = [
    "environmental impact of AI",
    "legal and regulatory issues with AI",
    "AI ethics and bias",
    "AI economic and labor impact",
    "AI geopolitics and national security",
    "AI in media and public opinion",
    "AI safety and existential risk",
]


def classify_batch(pipe, texts, candidate_labels):
    results = pipe(texts, candidate_labels, multi_label=False)
    if isinstance(results, dict):
        results = [results]
    return [
        {
            "label": r["labels"][0],
            "score": round(r["scores"][0], 3),
        }
        for r in results
    ]


def classify_articles(df):
    print("\n🤖 Running zero-shot classification...")
    print("   Loading facebook/bart-large-mnli (~1.6GB download on first run)...")
    
    from transformers import pipeline
    
    pipe = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,  # CPU; change to 0 if you have a CUDA GPU
    )
    
    texts = df["text"].tolist()
    primary_labels = []
    primary_scores = []
    
    print("   Step 1/2: Technical vs Non-Technical classification...")
    for i in tqdm(range(0, len(texts), CLASSIFICATION_BATCH_SIZE)):
        batch = texts[i : i + CLASSIFICATION_BATCH_SIZE]
        results = classify_batch(pipe, batch, CANDIDATE_LABELS_PRIMARY)
        for r in results:
            is_technical = "technical" in r["label"]
            primary_labels.append("TECHNICAL" if is_technical else "NON_TECHNICAL")
            primary_scores.append(r["score"])
    
    df["primary_label"] = primary_labels
    df["primary_score"] = primary_scores
    
    # Sub-classify only the non-technical ones
    non_tech_mask = df["primary_label"] == "NON_TECHNICAL"
    non_tech_texts = df.loc[non_tech_mask, "text"].tolist()
    non_tech_indices = df.index[non_tech_mask].tolist()
    
    print(f"\n   Found {len(non_tech_texts):,} non-technical articles")
    print("   Step 2/2: Sub-categorizing non-technical articles...")
    
    secondary_labels = [""] * len(df)
    secondary_scores = [0.0] * len(df)
    
    for i, (idx, text) in enumerate(tqdm(zip(non_tech_indices, non_tech_texts))):
        result = classify_batch(pipe, [text], CANDIDATE_LABELS_SECONDARY)[0]
        secondary_labels[idx] = result["label"]
        secondary_scores[idx] = result["score"]
    
    df["secondary_label"] = secondary_labels
    df["secondary_score"] = secondary_scores
    
    print("✅ Classification complete")
    return df


# ─────────────────────────────────────────────
# STEP 5: Write results back to DB
# ─────────────────────────────────────────────

def save_results(df):
    print(f"\n💾 Saving results to '{OUTPUT_TABLE}' table...")
    
    id_col = COLUMN_CONFIG["id"]
    output_df = df[[id_col, "cluster", "primary_label", "primary_score",
                     "secondary_label", "secondary_score"]].copy()
    
    conn = get_connection()
    
    if DB_TYPE == "sqlite":
        output_df.to_sql(OUTPUT_TABLE, conn, if_exists="replace", index=False)
    else:
        # For postgres, use pandas with SQLAlchemy
        from sqlalchemy import create_engine
        cfg = POSTGRES_CONFIG
        engine = create_engine(
            f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['database']}"
        )
        output_df.to_sql(OUTPUT_TABLE, engine, if_exists="replace", index=False)
    
    conn.close()
    print(f"✅ Results saved!")
    
    # Print summary
    print("\n📊 Classification Summary:")
    print(df["primary_label"].value_counts().to_string())
    print("\n🏷️  Non-Technical Sub-categories:")
    non_tech = df[df["primary_label"] == "NON_TECHNICAL"]
    if len(non_tech) > 0:
        print(non_tech["secondary_label"].value_counts().to_string())


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  AI Article Classifier Pipeline")
    print("=" * 55)
    
    # Load
    df = load_articles()
    
    # Embed
    embeddings = embed_articles(df)
    
    # Cluster (optional but useful for exploration)
    cluster_labels = cluster_articles(embeddings)
    df["cluster"] = cluster_labels
    sample_clusters(df, cluster_labels, n_samples=3)
    
    # Classify
    df = classify_articles(df)
    
    # Save
    save_results(df)
    
    print("\n✅ All done! Query your results:")
    print(f"""
    SELECT primary_label, secondary_label, COUNT(*) as count
    FROM {OUTPUT_TABLE}
    GROUP BY primary_label, secondary_label
    ORDER BY count DESC;
    """)
