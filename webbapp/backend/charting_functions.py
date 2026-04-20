from pandas import read_sql
import matplotlib.pyplot as plt
from matplotlib import use as plt_use
import seaborn as sns
from sqlite3 import connect
from datetime import datetime

DB_FILE = "../../db.sqlite"
TOPIC_LIST = ["code, software, development", "models, model, google", "just, like, work", "learning, machine, artificial", "enterprise, 2025, artificial"]
plt_use("agg")

def save_plot(filename, fig=None):

    if fig:
        fig.savefig(f"../frontend/images/{filename}", dpi=300, bbox_inches="tight")
        fig.clear()
        plt.close(fig)
    else:
        plt.savefig(f"../frontend/images/{filename}", dpi=300, bbox_inches="tight")
        plt.close()

    return f"/images/{filename}"


# Sentiment Distribution Over Length

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


def generate_sen_by_len_chart(data, filename="sen_by_len.png"):
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

    return save_plot(filename, fig)


# Dev Post Sentiment Distribution over Topic

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


def generate_sen_by_topic(data, filename="sen_by_topic.png"):
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

    return save_plot(filename)


# Topic Discussion Amount over Time
def get_topic_disc_over_time(post_per_month_threshold):
    query = f"""SELECT strftime('%Y-%m', published_at) month_released,
    SUM(IF(dominant_topic = 0, 1, 0)) topic_0,
    SUM(IF(dominant_topic = 1, 1, 0)) topic_1,
    SUM(IF(dominant_topic = 2, 1, 0)) topic_2,
    SUM(IF(dominant_topic = 3, 1, 0)) topic_3,
    SUM(IF(dominant_topic = 4, 1, 0)) topic_4
                    FROM DevPosts
                    where published_at < "2026-03-01"
                    GROUP BY month_released
                    HAVING COUNT(*) > {post_per_month_threshold}
                    ORDER BY month_released;"""

    conn = connect(DB_FILE)
    print("Running query")
    df = read_sql(query, conn)
    conn.close()
    df["month_released"] = df["month_released"].apply(lambda x: datetime.strptime(x, "%Y-%m"))
    for i in range(5):
        plt.plot(df["month_released"], df[f"topic_{i}"], label=f"Topic {i}: {TOPIC_LIST[i]} ")


def generate_topic_disc_over_time(data, filename="topic_disc_over_time.png"):
    post_per_month_threshold = int(data["params"].get("post_per_month_threshold", 5))
    get_topic_disc_over_time(post_per_month_threshold)
    plt.xlabel("Month")
    plt.ylabel("Topic")
    plt.title("Topic Change over Months")
    plt.xticks(rotation=90)
    plt.legend()

    return save_plot(filename)


# Get sentiment over month
def get_sentiment_change_over_months(table_name, column, sentiment_threshold=0, post_per_month_threshold=5):
    query = f"""SELECT strftime('%Y-%m', {column}) month_released,
    SUM(IF(roberta_pos_score - roberta_neg_score >= {sentiment_threshold}, 1, 0)) * 100 / count(*) positive,
    SUM(IF(roberta_pos_score - roberta_neg_score <= -{sentiment_threshold}, 1, 0)) * 100 / count(*) negative
                FROM {table_name}
                WHERE month_released BETWEEN "2021-01" AND "2025-12"
                GROUP BY month_released
                HAVING COUNT(*) > {post_per_month_threshold}
                ORDER BY month_released;"""
    conn = connect(DB_FILE)

    df = read_sql(query, conn)
    df["month_released"] = df["month_released"].apply(lambda x: datetime.strptime(x, "%Y-%m"))
    return df

def generate_sent_change_over_time(data, filename="sen_over_time.png"):
    sentiment_threshold = data["params"].get("sentiment_threshold", 0)
    post_per_month_threshold = data["params"].get("post_per_month_threshold", 5)
    articles_df = get_sentiment_change_over_months("modified_articles", "date", sentiment_threshold=sentiment_threshold, post_per_month_threshold=post_per_month_threshold)
    dp_df = get_sentiment_change_over_months("DevPosts", "published_at", sentiment_threshold=sentiment_threshold, post_per_month_threshold=post_per_month_threshold)

    plt.plot(articles_df["month_released"], articles_df["negative"], label="Negative News Articles")
    plt.plot(articles_df["month_released"], articles_df["positive"], label="Positive News Articles")

    plt.plot(dp_df["month_released"], dp_df["negative"], label="Negative DevPosts")
    plt.plot(dp_df["month_released"], dp_df["positive"], label="Positive DevPosts")
    plt.xlabel("Year")
    plt.ylabel("Sentiment %")
    plt.title("Sentiment Change over Year")
    plt.legend()
    save_plot(filename)


generate_sent_change_over_time({"params": {}}, filename="default_sen_over_time.png")