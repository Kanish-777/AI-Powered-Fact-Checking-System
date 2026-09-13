FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOME=/home/appuser
ENV HF_HOME=/home/appuser/.cache/huggingface

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /home/appuser/.cache/huggingface && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /home/appuser /app

USER appuser

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]