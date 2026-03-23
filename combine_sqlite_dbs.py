from os.path import isfile, isdir, join
from sqlite3 import connect
from pandas import read_csv
from os import listdir

def merge_news_data():
    news_dir = "news_data"
    output_file = "news_data/ai_articles.csv"

    if not isfile(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("url,date,title,text,sitename\n")
        for folder in sorted(listdir(news_dir)):
            dirpath = join(news_dir, folder)
            if not isdir(dirpath):
                continue

            for file in listdir(dirpath):
                filepath = join(dirpath, file)
                if not file.endswith(".csv"):
                    continue

                with open(filepath, "r", encoding="utf-8") as f:
                    file_lines = f.readlines()[1:] #[1:] to remove header

                with open(output_file, "a", encoding="utf-8") as f:
                    f.writelines(file_lines)

    csv_df = read_csv(output_file)
    conn = connect("db.sqlite")
    csv_df.to_sql("Articles", con=conn, if_exists="replace", index=False)



def main(source=None, dest=None):
    if not source:
        source = input("Enter the source sqlite database name: ")

    if not dest:
        dest = input("Enter the destination sqlite database name: ")

    conn = connect(source)
    c = conn.cursor()
    c.execute('select * from articles')
    rows = c.fetchall()
    c.close()
    conn.close()

    conn = connect(dest)
    c = conn.cursor()

    c.execute("""
              CREATE TABLE IF NOT EXISTS DevPosts (
                  post_id INT PRIMARY KEY,
                  title TEXT,
                  url TEXT,
                  published_at DATE,
                  tags TEXT,
                  body TEXT
              ) """)

    for row in rows:
        post_id, title, url, published_at, tags, body_text, impressions = row
        tags = tags.replace(",", "").replace(" ", ", ")

        c.execute("INSERT OR IGNORE INTO DevPosts VALUES (?, ?, ?, ?, ?, ?)",
                  (post_id, title, url, published_at, tags, body_text))

    layoffs = read_csv("layoffs.csv")
    layoffs.to_sql("Layoffs", con=conn, if_exists="replace", index=False)

    conn.commit()




if __name__ == "__main__":
    merge_news_data()
    main(source="dev_ai_articles_full.sqlite", dest="db.sqlite")