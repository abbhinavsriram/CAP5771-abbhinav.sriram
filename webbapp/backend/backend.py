from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

from charting_functions import generate_sen_by_len_chart, generate_sen_by_topic, generate_topic_disc_over_time, generate_sent_change_over_time
from similarity_search import EmbeddingPipeline

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "https://unaccusing-georgeanna-triboelectric.ngrok-free.dev",}}, supports_credentials=True)
CORS(app, resources={r"/*": {"origins": "http://localhost:5001",}}, supports_credentials=True)

# Initialize embedding pipeline on startup
print("⚡ Loading embeddings for similarity search...")
pipeline = None
try:
    pipeline = EmbeddingPipeline("../../db.sqlite")
    pipeline.load_embeddings_to_memory()
    print("✅ Embeddings loaded successfully")
except Exception as e:
    print(f"⚠️  Could not load embeddings: {e}")
    print("   Run: python similarity_search.py")


chart_dict = {
    "sen_by_topic": generate_sen_by_topic,
    "sen_by_len": generate_sen_by_len_chart,
    "sen_over_time": generate_sent_change_over_time,
    "topic_disc_over_time": generate_topic_disc_over_time,
}

@app.route('/', methods=['GET'])
def default():
    with open("../frontend/index.html", "r") as f:
        html_content = f.read()

    return html_content

@app.route('/app.js', methods=['GET'])
def app_js():
    with open(f"../frontend/app.js", "r") as f:
        js = f.read()
    return js

@app.route('/visualizations/<path:filename>', methods=['GET'])
def visualizations(filename):
    with open(f"../frontend/visualizations/{filename}", "r") as f:
        html_content = f.read()

    return html_content

@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    print("PATH:", request.path)

    try:
        data = request.get_json()
        print("DATA:", data)
        requested_chart = data['chart']

        function_to_call = chart_dict.get(requested_chart)

        if function_to_call is None:
            return jsonify({'error': 'Invalid chart'}), 400
        filepath = function_to_call(data)
        print("Sending response")
        return jsonify({
            'filepath': filepath,
            'input': data
        })

    except Exception as e:
        return jsonify({
            'error': str(e)}), 500

@app.route('/images/<path:filename>', methods=['GET'])
def serve_chart_image(filename):
    print(f"Getting image: {filename}")
    with open(f"../frontend/images/{filename}", "rb") as f:
        image_content = f.read()

    response = make_response()

    response.headers['Content-Type'] = 'image/png'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.status_code = 200
    response.data = image_content
    return response

@app.route('/favicon_io/<path:filename>', methods=['GET'])
def favicons(filename):
    with open(f"../frontend/favicon_io/{filename}", "rb") as f:
        image_content = f.read()

    response = make_response()
    filetype = filename.split(".")[-1]
    response.headers['Content-Type'] = f"image/{filetype}"
    response.status_code = 200
    response.data = image_content
    return response

@app.route('/find_similar', methods=['POST'])
def find_similar():
    """Find similar articles based on pasted text"""
    if pipeline is None:
        return jsonify({'error': 'Embeddings not loaded. Run similarity_search.py first.'}), 500

    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        top_k = data.get('top_k', 10)
        sentiment_threshold = data.get('sentiment_threshold', 0.3)

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        # Find similar articles
        results = pipeline.find_similar(
            text,
            top_k=top_k,
            sentiment_threshold=sentiment_threshold,
            show_scores=True
        )

        return jsonify(results)

    except Exception as e:
        print(f"Error in find_similar: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
