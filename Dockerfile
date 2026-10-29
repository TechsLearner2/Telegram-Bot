FROM python:3.12-slim
WORKDIR /app
COPY . .
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data/media
CMD python3 server.py & python3 telegram_bridge_cloud.py & wait
