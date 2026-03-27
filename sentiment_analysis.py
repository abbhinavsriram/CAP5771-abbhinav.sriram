from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from pandas import read_sql, read_csv
from sqlite3 import connect

def run_sentiment_analysis(table, column):
    con = connect("db.sqlite")
    df = read_sql(f"SELECT * FROM {table}", con)
    analyzer = SentimentIntensityAnalyzer()
    df["vader sentiment"] = df[column].apply(lambda x: analyzer.polarity_scores(x)["compound"])
    df["textblob sentiment"] = df[column].apply(lambda x: TextBlob(x).sentiment.polarity)
    con.commit()
    con.close()
    df.to_csv("temp.csv", index=False)
    # df = read_csv("temp.csv")
    con = connect("db.sqlite")
    df.to_sql(table, con, if_exists="replace", index=False)
    con.commit()
    con.close()

if __name__ == "__main__":
    # run_sentiment_analysis("Articles", "text")
    run_sentiment_analysis("DevPosts", "body_text")
