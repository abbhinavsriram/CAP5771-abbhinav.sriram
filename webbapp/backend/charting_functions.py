from pandas import read_sql
import matplotlib.pyplot as plt
from matplotlib import use as plt_use
from sqlite3 import connect
from datetime import datetime

DB_FILE = "../../db.sqlite"
NEWS_TOPIC_LIST = [
    "jobs, workers, employees",
    "data, security, cybersecurity",
    "generative, language, models",
    "tech, industry, world",
    "google, openai, microsoft",
    "business, companies, services",
    "people, think, human",
    "government, president, china"
]


DP_TOPIC_LIST = [
    "code, engineering, development",
    "openai, models, google",
    "tools, time, work",
    "ml, algorithms, artificial",
    "enterprise, companies, business",
    "customer, automation, chatbots",
    "financial, healthcare, predictive",
    "agentic, autonomous, workflows"
]



TABLE_TOPIC_LIST = {
    "modified_articles": NEWS_TOPIC_LIST,
    "devposts": DP_TOPIC_LIST
}

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

# Sentiment Distribution over Topic

def get_sent_by_topic(topic_choice, table_name):
    query = f"""SELECT SUM(CASE WHEN roberta_pos_score - roberta_neg_score >= 0 THEN 1 ELSE 0 END) * 100.0 / count(*) positive,
        SUM(CASE WHEN roberta_pos_score - roberta_neg_score <= 0 THEN 1 ELSE 0 END) * 100.0 / count(*) negative
                    FROM {table_name}
                    WHERE dominant_topic {'=' if topic_choice != -1 else '!='} {topic_choice}
                    GROUP BY dominant_topic;"""
    conn = connect(DB_FILE)

    df = read_sql(query, conn).transpose()
    conn.close()
    return df


def generate_sen_by_topic(data, filename="sen_by_topic.png"):
    topic_choice = int(data["params"].get("topic_choice", "-1"))
    table_name = data["params"].get("table_name", "modified_articles")

    df = get_sent_by_topic(topic_choice, table_name)
    if topic_choice == -1:
        df[0] = df.sum(axis=1)
        df = df[[0]]

    formal_table_name = "News Articles" if table_name == "modified_articles" else "Developer Posts"

    plt.pie(df[0], labels=["Positive", "Negative"], autopct="%1.1f%%")
    if topic_choice != -1:
        topic_list = TABLE_TOPIC_LIST[table_name.lower()]
        plt.title(f"{formal_table_name} Sentiment Analysis Percentage by Topic")
        plt.figtext(0.33, 0.05, f"Topic Keywords: {topic_list[int(topic_choice)]}")
    else:
        plt.title(f"{formal_table_name} Sentiment Analysis Percentage")

    save_plot(filename)


# Topic Discussion Amount over Time
def get_topic_disc_over_time(plot, post_per_month_threshold, table_name, date_column):
    query = f"""SELECT strftime('%Y-%m', {date_column}) month_released,
    SUM(CASE WHEN dominant_topic = 0 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_0,
    SUM(CASE WHEN dominant_topic = 1 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_1,
    SUM(CASE WHEN dominant_topic = 2 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_2,
    SUM(CASE WHEN dominant_topic = 3 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_3,
    SUM(CASE WHEN dominant_topic = 4 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_4,
    SUM(CASE WHEN dominant_topic = 5 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_5,
    SUM(CASE WHEN dominant_topic = 6 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_6,
    SUM(CASE WHEN dominant_topic = 7 THEN 1 ELSE 0 END) * 100.0 / count(*) topic_7
                    FROM {table_name}
                    GROUP BY month_released
                    HAVING COUNT(*) > {post_per_month_threshold}
                    ORDER BY month_released;"""

    conn = connect(DB_FILE)
    df = read_sql(query, conn)
    conn.close()

    df["month_released"] = df["month_released"].apply(lambda x: datetime.strptime(x, "%Y-%m"))

    formal_table_name = "News Articles" if table_name == "modified_articles" else "Developer Posts"
    plot.set_title(formal_table_name)
    for i in range(len(DP_TOPIC_LIST)):
        plot.plot(df["month_released"], df[f"topic_{i}"], label=f"Topic {i + 1}")
    plot.legend(loc="upper left", bbox_to_anchor=(1, 0.85), ncol=1, fontsize=10)


def generate_topic_disc_over_time(data, filename="topic_disc_over_time.png"):
    post_per_month_threshold = int(data["params"].get("post_per_month_threshold", 5))

    fig, axes = plt.subplots(2, 1, figsize=(9, 8))
    get_topic_disc_over_time(axes[0], post_per_month_threshold, "devposts", "published_at")
    get_topic_disc_over_time(axes[1], post_per_month_threshold, "modified_articles", "date")

    for ax in axes:
        ax.set_xlabel("")
        ax.set_ylabel("")
    fig.supylabel("% Topic Coverage")
    fig.suptitle("Normalized Topic Change over Months")
    fig.supxlabel("Month")

    # plt.xticks(rotation=90)
    # plt.legend()

    save_plot(filename, fig)


# Get sentiment over month
def get_sentiment_change_over_months(table_name, column, sentiment_threshold=0.0, post_per_month_threshold=5):
    query = f"""SELECT strftime('%Y-%m', {column}) AS month_released,
    SUM(CASE WHEN roberta_pos_score - roberta_neg_score >= {sentiment_threshold} THEN 1 ELSE 0 END) * 100.0 / count(*) positive,
    SUM(CASE WHEN roberta_pos_score - roberta_neg_score <= -1 * {sentiment_threshold} THEN 1 ELSE 0 END) * 100.0 / count(*) negative
                FROM {table_name}
                WHERE month_released BETWEEN "2021-01" AND "2025-12"
                GROUP BY month_released
                HAVING COUNT(*) > {post_per_month_threshold}
                ORDER BY month_released;"""
    conn = connect(DB_FILE)

    df = read_sql(query, conn)
    conn.close()
    df["month_released"] = df["month_released"].apply(lambda x: datetime.strptime(x, "%Y-%m"))
    return df

def generate_sent_change_over_time(data, filename="sen_over_time.png"):
    sentiment_threshold = data["params"].get("sentiment_threshold", 0)
    post_per_month_threshold = data["params"].get("post_per_month_threshold", 5)
    table_choice = data["params"].get("table_choice", "both")

    if table_choice == "both" or table_choice == "modified_articles":
        articles_df = get_sentiment_change_over_months("modified_articles", "date", sentiment_threshold=sentiment_threshold, post_per_month_threshold=post_per_month_threshold)
        plt.plot(articles_df["month_released"], articles_df["negative"], label="Negative News Articles")
        plt.plot(articles_df["month_released"], articles_df["positive"], label="Positive News Articles")

    if table_choice == "both" or table_choice == "devposts":
        dp_df = get_sentiment_change_over_months("DevPosts", "published_at", sentiment_threshold=sentiment_threshold, post_per_month_threshold=post_per_month_threshold)
        plt.plot(dp_df["month_released"], dp_df["negative"], label="Negative Dev Posts")
        plt.plot(dp_df["month_released"], dp_df["positive"], label="Positive Dev Posts")

    plt.xlabel("Year")
    plt.ylabel("Sentiment %")
    plt.title("Sentiment Change over Year")
    plt.xticks(rotation=90)
    plt.legend()
    save_plot(filename)


# Topic Discussion Amount over Time
def get_secondary_topic_disc_over_time(included_topics):
    topics = ["%discussion of AI in geopolitics, international competition, or national security%",
              "%discussion of AI safety, alignment, or existential risks%",
              "%discussion of AI's impact on jobs, employment, or the economy%",
              "%discussion of ethical concerns, bias, or fairness in AI systems%",
              "%discussion of how AI is portrayed in media or public opinion%",
              "%discussion of legal, regulatory, or policy issues related to AI%",
              "%discussion of the environmental impact or energy consumption of AI%"]
    topic_label = ["AI in geopolitics, international competition, or national security",
                   "AI safety, alignment, or existential risks",
                   "AI's impact on jobs, employment, or the economy",
                   "Ethical concerns, bias, or fairness in AI systems",
                   "How AI is portrayed in media or public opinion",
                   "Legal, regulatory, or policy issues related to AI",
                   "The environmental impact or energy consumption of AI"]
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    query = f"""SELECT strftime('%Y-%m', date) month_released,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_0,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_1,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_2,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_3,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_4,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_5,
    SUM(IIF(secondary_label like ?, 1, 0)) * 100.0 / count(*) topic_6
                    FROM modified_articles
                    GROUP BY month_released
                    HAVING COUNT(*) > 50
                    ORDER BY month_released;"""

    conn = connect(DB_FILE)
    df = read_sql(query, conn, params=topics)
    conn.close()

    df["month_released"] = df["month_released"].apply(lambda x: datetime.strptime(x, "%Y-%m"))

    for i in range(len(topics)):
        if included_topics[i]:
            plt.plot(df["month_released"], df[f"topic_{i}"], colors[i], label=topic_label[i])


def generate_secondary_topic_disc_over_time(data, filename="sec_news_topic_disc.png"):
    included_topics = data["params"].get("included_topics", [True, True, True, True, True, True, True])

    plt.figure(figsize=(10, 9))

    get_secondary_topic_disc_over_time(included_topics)

    plt.legend()
    plt.ylabel("Topic")
    plt.title("Normalized Topic Change In News Articles over Time")
    plt.xlabel("Month")

    # plt.xticks(rotation=90)
    # plt.legend()

    save_plot(filename)
