#!/bin/sh
set -e

# The Qdrant vectors and the policy_chunks rows in SQLite must come from the
# same ingestion run (vectors point at chunk ids), so the index is built
# inside the container on first start and kept in volumes after that.
MARKER=/app/qdrant_data/.ingested
if [ ! -f "$MARKER" ]; then
  echo "[entrypoint] Building the policy RAG index (first start only)..."
  # No --reset: it rmtree()s /app/qdrant_data, which is a volume mount point
  # here. The volume starts empty and ingestion is idempotent, so it isn't needed.
  if python scripts/ingest_policies.py; then
    touch "$MARKER"
  else
    echo "[entrypoint] Ingestion failed; chat will fall back to keyword search." >&2
  fi
fi

exec "$@"
