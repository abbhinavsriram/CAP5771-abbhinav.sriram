import sqlite3
import argparse
import pandas as pd
import numpy as np
import pickle
import base64
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob


class EmbeddingPipeline:

    def __init__(self, db_path="../../db.sqlite", model_name="all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self.model = None
        self.news_embeddings_cache = None
        self.devpost_embeddings_cache = None
        self.devpost_cache = None
        self.news_cache = None

    @staticmethod
    def textblob_sentiment(text):
        """Return TextBlob polarity, subjectivity, and sentiment label."""
        if not isinstance(text, str) or not text.strip():
            return 0.0, 0.0, "neutral"

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if polarity > 0.05:
            label = "positive"
        elif polarity < -0.05:
            label = "negative"
        else:
            label = "neutral"

        return polarity, subjectivity, label

    @staticmethod
    def _json_safe(value):
        """Convert NumPy/pandas scalars and containers into JSON-safe Python types."""
        if isinstance(value, dict):
            return {key: EmbeddingPipeline._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [EmbeddingPipeline._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [EmbeddingPipeline._json_safe(item) for item in value]
        if isinstance(value, np.generic):
            return value.item()
        return value

    def load_model(self):
        print("Loading embedding model")

        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def get_all_articles(self, table):
        """Load all articles from database"""
        conn = sqlite3.connect(self.db_path)


        df = None
        conn.execute(f"SELECT * FROM {table} LIMIT 1")
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        table_name = table
        conn.close()

        if df is None:
            raise ValueError(f"Could not find article table in {self.db_path}")

        print(f"   Loaded {len(df):,} articles")
        return df, table_name



    def combine_text(self, row, max_chars=1500):
        """Combine title and body for embedding"""
        title = str(row.get("title", "") or "")
        body = str(row.get("body", "") or row.get("body_text", "") or "")
        combined = (title + " " + body[:max_chars]).strip()
        return combined if combined else "No content"

    def generate_embeddings(self, df, batch_size=64):
        """Generate embeddings for all articles in dataframe"""
        self.load_model()

        print(f"\n📝 Preparing texts...")
        texts = df.apply(self.combine_text, axis=1).tolist()

        print(f"🔢 Generating embeddings for {len(texts):,} articles...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

        print(f"Embeddings shape: {embeddings.shape}")
        return embeddings

    def encode_embeddings(self, embeddings):
        """Convert numpy arrays to base64-encoded pickle for SQLite storage"""
        print("\n🔐 Encoding embeddings for database...")
        encoded = []
        for emb in tqdm(embeddings, desc="Encoding"):
            pickled = pickle.dumps(emb.astype("float32"))
            b64 = base64.b64encode(pickled).decode("utf-8")
            encoded.append(b64)
        return encoded

    def decode_embedding(self, emb_b64):
        """Decode a single base64-encoded embedding back to numpy"""
        pickled = base64.b64decode(emb_b64)
        emb = pickle.loads(pickled)
        return emb

    def run_pipeline(self, save_embeddings=True, table=None):
        """Run the complete pipeline: load, embed, encode, save"""
        if not table:
            raise ValueError("A table name is required for run_pipeline")

        print("=" * 60)
        print("  Embedding Pipeline")
        print("=" * 60)

        # Load articles
        df, table_name = self.get_all_articles(table)

        # Check if embeddings column exists
        if "embedding" in df.columns:
            print("\n⚠️  'embedding' column already exists. Regenerating...")

        # Generate embeddings
        embeddings = self.generate_embeddings(df)

        # Encode for database
        encoded_embeddings = self.encode_embeddings(embeddings)
        df["embedding"] = encoded_embeddings

        # Save to database
        if save_embeddings:
            self.save_to_db(df, table_name)

        return df, table_name

    def run_pipeline_for_tables(self, tables, save_embeddings=True):
        """Run embeddings pipeline for multiple tables."""
        if not tables:
            raise ValueError("At least one table is required")

        completed_tables = []
        failed_tables = []

        for table in tables:
            print("\n" + "-" * 60)
            print(f"Processing table: {table}")
            print("-" * 60)
            try:
                self.run_pipeline(save_embeddings=save_embeddings, table=table)
                completed_tables.append(table)
            except Exception as e:
                print(f"Failed table '{table}': {e}")
                failed_tables.append({"table": table, "error": str(e)})

        return {"completed_tables": completed_tables, "failed_tables": failed_tables}

    def save_to_db(self, df, table_name):
        """Save dataframe with embeddings back to database"""
        conn = sqlite3.connect(self.db_path)

        print(f"\n💾 Saving {len(df):,} articles with embeddings to '{table_name}'...")
        df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Verify
        count = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {table_name}", conn)
        print(f"Saved {count.iloc[0]['cnt']:,} rows")

        conn.close()

    def load_embeddings_to_memory(self):
        """Load all embeddings from DB into memory for fast search"""
        if self.news_embeddings_cache is not None:
            return  # Already loaded

        print("\n⚡ Loading embeddings into memory...")
        conn = sqlite3.connect(self.db_path)

        devpost_query = """
            SELECT title, body_text, embedding,
                   dominant_topic, secondary_label,
                   tb_polarity, tb_subjectivity, tb_sentiment
            FROM DevPosts
            WHERE embedding IS NOT NULL
        """
        news_query = """
            SELECT title, text, embedding,
                   dominant_topic, secondary_label,
                   tb_polarity, tb_subjectivity, tb_sentiment
            FROM modified_articles
            WHERE embedding IS NOT NULL
        """
        self.devpost_cache = pd.read_sql_query(devpost_query, conn)
        self.news_cache = pd.read_sql_query(news_query, conn)
        conn.close()

        print(f"Decoding {len(self.devpost_cache):,} embeddings...")
        devpost_embeddings = []
        for emb_b64 in tqdm(self.devpost_cache["embedding"]):
            try:
                devpost_embeddings.append(self.decode_embedding(emb_b64))
            except Exception as e:
                print(f"Failed to decode: {e}")
                devpost_embeddings.append(np.zeros(384))

        self.devpost_embeddings_cache = np.array(devpost_embeddings)


        news_embeddings = []
        for emb_b64 in tqdm(self.news_cache["embedding"]):
            try:
                news_embeddings.append(self.decode_embedding(emb_b64))
            except Exception as e:
                print(f"Failed to decode: {e}")
                news_embeddings.append(np.zeros(384))

        self.news_embeddings_cache = np.array(news_embeddings)
        print(f"✅ Ready for similarity search")

    def find_similar(
        self, query_text, top_k=3, show_scores=False
    ):
        """
        Find similar articles based on semantic similarity and sentiment.

        Args:
            query_text: The article text to find matches for
            top_k: Number of results to return
            show_scores: Include detailed scores in results

        Returns:
            List of similar articles with metadata
        """
        if self.news_embeddings_cache is None or self.devpost_embeddings_cache is None:
            self.load_embeddings_to_memory()

        # Embed query
        self.load_model()
        query_embedding = self.model.encode(query_text, convert_to_numpy=True)

        # Compute semantic similarity
        news_similarities = cosine_similarity(
            [query_embedding], self.news_embeddings_cache
        )[0]

        devpost_similarities = cosine_similarity(
            [query_embedding], self.devpost_embeddings_cache
        )[0]

        # Normalize to 0-1
        devpost_similarities = (devpost_similarities + 1) / 2
        news_similarities = (news_similarities + 1) / 2

        # Get sentiment of query using TextBlob polarity.
        query_polarity, query_subjectivity, query_label = self.textblob_sentiment(query_text[:1000])


        # Get top-k
        top_news_indices = np.argsort(news_similarities)[::-1][:top_k]
        top_devpost_indices = np.argsort(devpost_similarities)[::-1][:top_k]

        news_res = []
        for idx in top_news_indices:
            if news_similarities[idx] == 0:
                continue  # Skip filtered articles

            row = self.news_cache.iloc[idx]
            result = {
                "title": row["title"],
                "similarity_score": float(news_similarities[idx]),
                "dominant_topic": self._json_safe(row.get("dominant_topic", "")),
                "secondary_label": row.get("secondary_label", ""),
                "tb_polarity": float(row.get("tb_polarity", 0.0)),
                "tb_subjectivity": float(row.get("tb_subjectivity", 0.0)),
                "tb_sentiment": self._json_safe(row.get("tb_sentiment", 0.0))

            }

            if show_scores:
                result["query_polarity"] = float(query_polarity)
                result["query_subjectivity"] = float(query_subjectivity)
                result["query_sentiment_label"] = query_label

            news_res.append(result)

        devpost_res = []
        for idx in top_devpost_indices:
            if devpost_similarities[idx] == 0:
                continue  # Skip filtered articles

            row = self.devpost_cache.iloc[idx]
            result = {
                "title": row["title"],
                "similarity_score": float(devpost_similarities[idx]),
                "dominant_topic": self._json_safe(row.get("dominant_topic", "")),
                "secondary_label": row.get("secondary_label", ""),
                "tb_polarity": float(row.get("tb_polarity", 0.0)),
                "tb_subjectivity": float(row.get("tb_subjectivity", 0.0)),
                "tb_sentiment": self._json_safe(row.get("tb_sentiment", 0.0))
            }

            if show_scores:
                result["query_polarity"] = float(query_polarity)
                result["query_subjectivity"] = float(query_subjectivity)
                result["query_sentiment_label"] = query_label

            devpost_res.append(result)

        query_sentiment = {
            "tb_polarity": float(query_polarity),
            "tb_subjectivity": float(query_subjectivity),
            "tb_sentiment": query_label
        }
        return self._json_safe({"news": news_res, "devpost": devpost_res, "query_sentiment": query_sentiment})


# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and save embeddings for DB tables")
    parser.add_argument("--db-path", default="../../db.sqlite", help="Path to sqlite database")
    parser.add_argument(
        "--tables",
        nargs="+",
        default=None,
        help="Table names to process (example: --tables article_classifications DevPosts)",
    )
    args = parser.parse_args()

    pipeline = EmbeddingPipeline(db_path=args.db_path)
    tables = args.tables

    if not tables:
        raise ValueError("No tables found in database. Use --tables to pass table names explicitly.")

    print(f"Selected tables: {tables}")
    summary = pipeline.run_pipeline_for_tables(tables=tables, save_embeddings=True)

    print("\n" + "=" * 60)
    print("Embedding generation complete")
    print("=" * 60)
    print(f"Completed: {summary['completed_tables']}")
    if summary["failed_tables"]:
        print(f"Failed: {summary['failed_tables']}")
