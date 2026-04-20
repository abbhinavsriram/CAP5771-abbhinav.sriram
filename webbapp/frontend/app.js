function update_slider_output(slider_id, output_prefix) {
    let slider = $("#" + slider_id);
    let output = $("#output_" + slider_id);
    output.html(output_prefix + slider.val());
}

async function generate_chart(chart_name, params) {
    let chart = $("#" + chart_name)
    console.log("Got object " + chart)
    let body = JSON.stringify({
        "chart": chart_name,
        "params": params,
    })

    let url = "http://127.0.0.1:5001/generate_chart";
    console.log("Sending request to " + url)
    console.log("With body: " + body)
    let request = {
                    method: "POST",
                    credentials: "include",
                    mode: "cors",
                    body: body,
                    headers: {"content-type": "application/json"}
                };

    try {
        chart.html("<div class=\"loader\"></div>\n")
        const response = await fetch(url, request);
        if (!response.ok) {
            alert(`Response status: ${response.status}`);
        } else {
            let response_json = await response.json();
            let filepath = response_json['filepath'] + "?t=" + new Date().getTime()

            console.log("Response: " + filepath)
            chart.html(`<img src="${filepath}" alt="${chart_name}" class="img-fluid">`);
        }
    } catch (error) {
        chart.innerHTML = "Error: " + error
        console.log("Erred")
        alert(error);
    }
}

async function generate_sen_by_len_chart() {
    let sentiment_threshold = $("#sentiment_threshold").val()
    let news_length_threshold = $("#news_length_threshold").val()
    let devposts_length_threshold = $("#devposts_length_threshold").val()

    let params = {
        "sentiment_threshold": sentiment_threshold,
        "news_length_threshold": news_length_threshold,
        "devposts_length_threshold": devposts_length_threshold
    }

    await generate_chart("sen_by_len", params)
}

async function generate_sen_by_topic_chart() {
    let topic_choice = $("#topic-choice").val()

    let params = {
        "topic_choice": topic_choice,
    }

    await generate_chart("sen_by_topic", params)
}