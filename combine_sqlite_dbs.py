from sqlite3 import connect

def main(source_sqlite=None, destination_sqlite=None):
    if not source_sqlite:
        source_sqlite = input("Enter the source sqlite database name: ")

    if not destination_sqlite:
        destination_sqlite = input("Enter the destination sqlite database name: ")

    conn = connect(source_sqlite)
    c = conn.cursor()
    c.execute('select * from articles')
    rows = c.fetchall()
    c.close()
    conn.close()

    conn = connect(destination_sqlite)
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

        c.execute("INSERT INTO DevPosts VALUES (?, ?, ?, ?, ?, ?)",
                  (post_id, title, url, published_at, tags, body_text))

    conn.commit()


if __name__ == "__main__":
    main()