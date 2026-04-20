from pandas import read_sql
import matplotlib.pyplot as plt
from matplotlib import use as plt_use
import seaborn as sns
from sqlite3 import connect

DB_FILE = "../../db.sqlite"
TOPIC_LIST = ["code, software, development", "models, model, google", "just, like, work", "learning, machine, artificial", "enterprise, 2025, artificial"]
plt_use("agg")

def get_sentiment_dist_over_length(table_name, column, date_column, sentiment_threshold=0.0, length_threshold=500000):
    query = f"""SELECT {column}, IF(roberta_pos_score - roberta_neg_score > {sentiment_threshold}, 'positive', 'negative') sentiment, strftime('%Y-%m', {date_column}) month_released
                FROM {table_name}
                WHERE month_released BETWEEN "2021-01" AND "2025-12"
                ORDER BY month_released, strftime('%m', {date_column});"""
    conn = connect(DB_FILE)

    df = read_sql(query, conn)
    df["length"] = df[column].apply(len)
    df = df[df["length"] < length_threshold]
    return df


def generate_sen_by_len_chart(data, filename="sentiment_dist_over_length.png"):
    print("Got data", data)
    sentiment_threshold = float(data["params"].get("sentiment_threshold", 0))
    news_length_threshold = int(data["params"].get("news_length_threshold", 55000))
    devposts_length_threshold = int(data["params"].get("devposts_length_threshold", 55000))


    articles_df = get_sentiment_dist_over_length("modified_articles", "text", date_column="date",
                                                 sentiment_threshold=sentiment_threshold,
                                                 length_threshold=news_length_threshold)
    dp_df = get_sentiment_dist_over_length("DevPosts", "body_text", date_column="published_at",
                                           sentiment_threshold=sentiment_threshold,
                                           length_threshold=devposts_length_threshold)


    fig, axes = plt.subplots(1, 2, figsize=(9, 5))
    sns.boxplot(x="sentiment", y='length', data=articles_df, ax=axes[0])

    sns.boxplot(x="sentiment", y='length', data=dp_df, ax=axes[1])
    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
    axes[0].set_title("News Articles Sentiment Distribution by Length")
    axes[1].set_title("DevPosts Sentiment Distribution by Length")
    fig.supylabel("Length (chars)")
    fig.supxlabel("Sentiment")

    chart_filepath = f"../frontend/images/{filename}"
    fig.savefig(chart_filepath, dpi=300, bbox_inches="tight")
    fig.clear()
    plt.close(fig)
    return chart_filepath


def get_sent_by_topic(topic_choice):
    query = f"""SELECT SUM(IF(roberta_pos_score - roberta_neg_score >= 0, 1, 0)) * 100 / count(*) positive,
            SUM(IF(roberta_pos_score - roberta_neg_score <= 0, 1, 0)) * 100 / count(*) negative
                    FROM DevPosts
                    WHERE dominant_topic {'=' if topic_choice != -1 else '!='} {topic_choice}
                    GROUP BY dominant_topic;"""
    conn = connect(DB_FILE)

    df = read_sql(query, conn).transpose()
    conn.close()
    return df


def generate_sen_by_topic(data, filename="sentiment_by_topic.png"):
    topic_choice = int(data["params"].get("topic_choice", "-1"))

    df = get_sent_by_topic(topic_choice)
    if topic_choice == -1:
        df[0] = df.sum(axis=1)
        df = df[[0]]

    plt.pie(df[0], labels=["Positive", "Negative"], autopct="%1.1f%%")
    if topic_choice != -1:
        plt.title("Developer Posts Sentiment Analysis Percentage by Topic")
        plt.figtext(0.33, 0.05, f"Topic Keywords: {TOPIC_LIST[int(topic_choice)]}")
    else:
        plt.title("Developer Posts Sentiment Analysis Percentage")

    chart_filepath = f"../frontend/images/{filename}"
    plt.savefig(chart_filepath, dpi=300, bbox_inches="tight")
    plt.close()

    return chart_filepath

