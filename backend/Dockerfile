FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    gcc \
    g++ \
    curl \
    locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/es_ES.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

RUN mkdir -p /app/chroma_db /app/logs /chroma/chroma_db

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENV LANG=es_ES.UTF-8
ENV LC_ALL=es_ES.UTF-8
ENV LANGUAGE=es_ES:es

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

