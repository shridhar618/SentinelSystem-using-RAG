FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/opt/hf-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-rag.txt ./
# CPU-only PyTorch: the default Linux wheel pulls in several GB of CUDA libraries.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements-rag.txt

# Bake the embedding model into the image so the first query doesn't download it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

RUN mkdir -p /app/instance /app/app/data /app/qdrant_data \
    && chmod +x /app/docker-entrypoint.sh

EXPOSE 5001

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "app.py"]
