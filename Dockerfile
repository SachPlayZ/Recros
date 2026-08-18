FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/apps/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
RUN pip install --no-cache-dir -r /app/apps/api/requirements.txt

COPY apps/api /app/apps/api
COPY apps/web /app/apps/web
COPY ml/artifacts /app/ml/artifacts
COPY movie_dataset/movies_metadata.csv /app/movie_dataset/movies_metadata.csv
COPY music_dataset/data_music.csv /app/music_dataset/data_music.csv
COPY book_dataset/book_data.csv /app/book_dataset/book_data.csv
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
RUN chmod +x /app/docker/entrypoint.sh

ENV RECROS_DB=/app/apps/api/data/recros.db \
    RECROS_WEB_DIR=/app/apps/web \
    RECROS_SEED_LIMIT=800

EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
