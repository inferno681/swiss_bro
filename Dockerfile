FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates \
    libglib2.0-0 libnss3 libnss3-tools libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libexpat1 libatspi2.0-0 libx11-6 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxkbcommon0 \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONUNBUFFERED=1

ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false

RUN poetry install --only main --no-interaction --no-ansi --no-root

RUN playwright install

RUN mkdir -p ./src

COPY ./src/config  ./src/config

COPY ./src/bot  ./src/bot

ENV PYTHONPATH=/app/src/

CMD ["python", "src/bot/main.py"]
