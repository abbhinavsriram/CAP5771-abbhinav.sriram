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

        if (!results || results.length === 0) {
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
    const resultsList = $("#results-list");

    resultsList.empty();

    results.forEach((result, index) => {
        const card = create_result_card(result, index + 1);
        resultsList.append(card);
    });

    resultsContainer.show();
}

function create_result_card(result, rank) {
    const sentimentClass = get_sentiment_class(result.sentiment);
    const sentimentText = get_sentiment_text(result.sentiment);

    let labelsHtml = "";
    if (result.primary_label) {
        labelsHtml += `<span class="label-badge label-primary">${result.primary_label}</span>`;
    }
    if (result.secondary_label) {
        labelsHtml += `<span class="label-badge label-secondary">${result.secondary_label}</span>`;
    }

    const card = `
        <div class="result-card">
            <div class="result-item">
                <div class="result-rank">#${rank}</div>
                <div class="result-content">
                    <div class="result-title">${escape_html(result.title)}</div>
                    <div class="result-score">
                        ✓ ${(result.similarity_score * 100).toFixed(1)}% Match
                    </div>
                    <div class="result-labels">
                        ${labelsHtml}
                        <span class="sentiment-badge ${sentimentClass}">${sentimentText}</span>
                    </div>
                    <div class="result-meta">
                        <span><strong>Sentiment Score:</strong> ${(result.sentiment * 100).toFixed(1)}%</span>
                        <span><strong>ID:</strong> ${result.id}</span>
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
        return "😊 Positive";
    } else if (sentiment <= -0.05) {
        return "😞 Negative";
    } else {
        return "😐 Neutral";
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
    return text.replace(/[&<>"']/g, m => map[m]);
}

function show_loading() {
    $("#loading").show();
    $("#search-text").text("🔄 Searching...");
    $(".btn-search").prop("disabled", true);
}

function hide_loading() {
    $("#loading").hide();
    $("#search-text").text("🔎 Find Similar Articles");
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
}

function hide_results() {
    $("#results-container").hide();
    $("#no-results").hide();
}

// Allow Enter key to trigger search (Ctrl+Enter or Cmd+Enter)
$("#article-input").keydown(function(event) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        search_similar_articles();
    }
});
