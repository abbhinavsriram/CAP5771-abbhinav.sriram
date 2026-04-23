/**
 * Similarity Search Frontend
 * Handles article paste, search submission, and results display
 */

// Update sentiment threshold display
$("#sentiment-threshold").on("input", function() {
    $("#sentiment-output").text($(this).val());
});

async function search_similar_articles() {
    const articleText = $("#article-input").val().trim();

    // Validation
    if (!articleText) {
        show_error("Please paste an article to search.");
        return;
    }

    if (articleText.length < 50) {
        show_error("Please paste a longer article (at least 50 characters).");
        return;
    }

    const topK = parseInt($("#top-k").val());
    const sentimentThreshold = parseFloat($("#sentiment-threshold").val());

    if (isNaN(topK) || topK < 1) {
        show_error("Please enter a valid number of results.");
        return;
    }

    // Show loading state
    show_loading();
    hide_results();
    hide_error();

    try {
        // Make request to backend
        const response = await fetch("http://127.0.0.1:5001/find_similar", {
            method: "POST",
            credentials: "include",
            mode: "cors",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                text: articleText,
                top_k: topK,
                sentiment_threshold: sentimentThreshold
            })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const results = await response.json();

        if (!results || (!results.news || results.news.length === 0) && (!results.devpost || results.devpost.length === 0)) {
            show_no_results();
        } else {
            display_results(results);
        }

    } catch (error) {
        console.error("Error:", error);
        show_error(`Error finding similar articles: ${error.message}`);
    } finally {
        hide_loading();
    }
}

function display_results(results) {
    const resultsContainer = $("#results-container");
    const querySummary = $("#query-summary");
    const newsSection = $("#news-results-section");
    const devpostSection = $("#devpost-results-section");
    const newsResultsList = $("#news-results-list");
    const devpostResultsList = $("#devpost-results-list");

    querySummary.empty().hide();
    newsResultsList.empty();
    devpostResultsList.empty();

    if (results.query_sentiment) {
        querySummary.html(create_query_summary(results.query_sentiment)).show();
    }

    if (results.news && results.news.length > 0) {
        results.news.forEach((result, index) => {
            newsResultsList.append(create_result_card(result, index + 1, "news"));
        });
        newsSection.show();
    } else {
        newsSection.hide();
    }

    if (results.devpost && results.devpost.length > 0) {
        results.devpost.forEach((result, index) => {
            devpostResultsList.append(create_result_card(result, index + 1, "devpost"));
        });
        devpostSection.show();
    } else {
        devpostSection.hide();
    }

    resultsContainer.show();
}

function create_query_summary(querySentiment) {
    const sentimentValue = typeof querySentiment.tb_polarity === "number" ? querySentiment.tb_polarity : 0;
    const sentimentClass = get_sentiment_class(sentimentValue);
    const sentimentText = get_sentiment_text(sentimentValue);
    const subjectivity = typeof querySentiment.tb_subjectivity === "number" ? querySentiment.tb_subjectivity : 0;
    const label = querySentiment.tb_sentiment || "neutral";

    return `
        <div class="result-card">
            <div class="result-title">Query Sentiment</div>
            <div class="result-labels">
                <span class="sentiment-badge ${sentimentClass}">${sentimentText}</span>
            </div>
            <div class="result-meta">
                <span><strong>Polarity:</strong> ${(sentimentValue * 100).toFixed(1)}%</span>
                <span><strong>Subjectivity:</strong> ${(subjectivity * 100).toFixed(1)}%</span>
                <span><strong>Label:</strong> ${escape_html(String(label))}</span>
            </div>
        </div>
    `;
}

function create_result_card(result, rank, resultType) {
    const sentimentValue = typeof result.tb_polarity === "number" ? result.tb_polarity : 0;
    const sentimentClass = get_sentiment_class(sentimentValue);
    const sentimentText = get_sentiment_text(sentimentValue);
    const polarity = typeof result.tb_polarity === "number" ? result.tb_polarity : 0;
    const subjectivity = typeof result.tb_subjectivity === "number" ? result.tb_subjectivity : 0;

    let labelsHtml = "";
    if (result.dominant_topic !== undefined && result.dominant_topic !== null && result.dominant_topic !== "") {
        labelsHtml += `<span class="label-badge label-primary">Topic: ${escape_html(String(result.dominant_topic))}</span>`;
    }
    if (result.secondary_label) {
        labelsHtml += `<span class="label-badge label-secondary">${escape_html(String(result.secondary_label))}</span>`;
    }

    const scoreLabel = resultType === "news" ? "News Match" : "Developer Match";
    const sectionLabel = resultType === "news" ? "News" : "Developer";

    const card = `
        <div class="result-card">
            <div class="result-item">
                <div class="result-rank">#${rank}</div>
                <div class="result-content">
                    <div class="result-title">${escape_html(result.title)}</div>
                    <div class="result-score">
                        ✓ ${scoreLabel}: ${(result.similarity_score * 100).toFixed(1)}%
                    </div>
                    <div class="result-labels">
                        ${labelsHtml}
                        <span class="sentiment-badge ${sentimentClass}">${sentimentText}</span>
                    </div>
                    <div class="result-meta">
                        <span><strong>Polarity:</strong> ${(polarity * 100).toFixed(1)}%</span>
                        <span><strong>${sectionLabel} Sentiment:</strong> ${(sentimentValue * 100).toFixed(1)}%</span>
                        <span><strong>Subjectivity:</strong> ${(subjectivity * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    return card;
}

function get_sentiment_class(sentiment) {
    if (sentiment >= 0.05) {
        return "sentiment-positive";
    } else if (sentiment <= -0.05) {
        return "sentiment-negative";
    } else {
        return "sentiment-neutral";
    }
}

function get_sentiment_text(sentiment) {
    if (sentiment >= 0.05) {
        return "Positive";
    } else if (sentiment <= -0.05) {
        return "Negative";
    } else {
        return "Neutral";
    }
}

function escape_html(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

function show_loading() {
    $("#loading").show();
    $("#search-text").text("Searching...");
    $(".btn-search").prop("disabled", true);
}

function hide_loading() {
    $("#loading").hide();
    $("#search-text").text("Find Similar Articles");
    $(".btn-search").prop("disabled", false);
}

function show_error(message) {
    $("#error-text").text(message);
    $("#error-message").show();
}

function hide_error() {
    $("#error-message").hide();
}

function show_no_results() {
    $("#no-results").show();
    $("#results-container").hide();
    $("#query-summary").hide();
}

function hide_results() {
    $("#results-container").hide();
    $("#no-results").hide();
    $("#query-summary").hide();
    $("#news-results-section").hide();
    $("#devpost-results-section").hide();
}

// Allow Enter key to trigger search (Ctrl+Enter or Cmd+Enter)
$("#article-input").keydown(function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        search_similar_articles();
    }
});
