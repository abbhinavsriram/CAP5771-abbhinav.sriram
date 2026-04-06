from pandas import read_csv, read_sql
from os.path import isdir, join
from sqlite3 import connect
from os import listdir

def merge_news_data(news_dir="news_data", output_db="db.sqlite"):
    conn = connect(output_db)

    for folder in sorted(listdir(news_dir)):
        dirpath = join(news_dir, folder)
        if not isdir(dirpath):
            continue

        for file in listdir(dirpath):
            filepath = join(dirpath, file)
            if not file.endswith(".csv"):
                continue

            csv_file = read_csv(filepath)
            csv_file.to_sql("Articles", con=conn, if_exists="append", index=False)


def main(source_db=None, source_table=None, dest=None):
    if not source_db:
        source_db = input("Enter the source sqlite database name: ")

    if not dest:
        dest = input("Enter the destination sqlite database name: ")

    layoffs = read_csv("layoffs.csv")
    conn = connect(source_db)
    devposts = read_sql(f"SELECT h.id, h.title, h.body_text, h.url, h.published_at, s.cluster, s.primary_score, s.primary_label, s.secondary_score, s.secondary_label, s.dominant_topic, s.dominant_topic_prob, s.roberta_pos_score, s.roberta_neg_score FROM sentiment_articles s join hashnode_articles h on s.id=h.id", conn)
    conn.close()
    devposts["roberta_score"] = devposts["roberta_pos_score"] - devposts["roberta_neg_score"]
    # devposts["tags"] = devposts["tags"].apply(lambda x: x.replace(",,,", ";").replace(",", "").replace(";", ","))
    conn = connect(dest)
    devposts.to_sql("DevPosts", con=conn, if_exists="delete_rows", index=False)
    layoffs.to_sql("Layoffs", con=conn, if_exists="delete_rows", index=False)
    conn.close()


if __name__ == "__main__":
    # merge_news_data()
    main(source_db="dev_ai_articles_full.sqlite", source_table="sentiment_articles natural join `topic labeled articles`", dest="db.sqlite")