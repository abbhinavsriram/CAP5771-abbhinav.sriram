# IMPORTANT
# To have the webapp run in a docker container make the following changes:
# Remove all ../ from backend, i.e. all file references should be top level
# Change CORS to HOSTED URL in backend/backend.py
# Update url in app.js and similarity_search.js to HOSTED URL

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors sentence-transformers scikit-learn matplotlib seaborn vadersentiment textblob

COPY webapp .

COPY db.sqlite /app/db.sqlite

EXPOSE 5001

CMD ["python", "-u", "backend/backend.py"]