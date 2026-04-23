FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask flask-cors sentence-transformers scikit-learn matplotlib seaborn vadersentiment textblob

COPY webapp .

COPY db.sqlite /app/db.sqlite

EXPOSE 5001

CMD ["python", "-u", "backend/backend.py"]