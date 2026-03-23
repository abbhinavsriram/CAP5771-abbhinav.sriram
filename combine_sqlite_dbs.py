from os.path import isfile, isdir, join
from pandas import read_csv, read_sql
from sqlite3 import connect
from os import listdir

def merge_news_data(news_dir="news_data", output_db="db.sqlite"):
    output_file = join(news_dir, "ai_articles.csv")

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
    conn = connect(output_db)
    csv_df.to_sql("Articles", con=conn, if_exists="delete_rows", index=False)


def main(source=None, dest=None):
    if not source:
        source = input("Enter the source sqlite database name: ")

    if not dest:
        dest = input("Enter the destination sqlite database name: ")

    layoffs = read_csv("layoffs.csv")
    conn = connect(source)
    devposts = read_sql("SELECT * FROM articles", conn)
    conn.close()

    conn = connect(dest)
    devposts.to_sql("DevPosts", con=conn, if_exists="delete_rows", index=False)
    layoffs.to_sql("Layoffs", con=conn, if_exists="delete_rows", index=False)
    conn.close()


if __name__ == "__main__":
    merge_news_data()
    main(source="dev_notebooks/dev_ai_articles_full.sqlite", dest="db.sqlite")