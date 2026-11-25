from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

import numpy as np

log = logging.getLogger(__name__)

DEFAULT_LOCAL_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"


def item_text(row: Any) -> str:
    """Build stable, cross-domain text for an item embedding."""
    def value(key: str) -> str:
        try:
            raw = row[key]
        except (KeyError, TypeError):
            raw = ""
        if raw is None:
            return ""
        try:
            if bool(np.isnan(raw)):
                return ""
        except (TypeError, ValueError):
            pass
        return str(raw).strip()

    domain = value("domain")
    title = value("title")
    description = value("description")
    creators = value("creators")
    genres = value("genres_str") or value("genres")
    tags = value("tags_str") or value("tags")
    fields = [
        f"domain: {domain}" if domain else "",
        f"title: {title}" if title else "",
        f"creator: {creators}" if creators else "",
        f"genres: {genres.replace('|', ', ')}" if genres else "",
        f"tags: {tags.replace('|', ', ')}" if tags else "",
        f"description: {description}" if description else "",
    ]
    return "\n".join(field for field in fields if field)


def normalize(matrix: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, 1e-12)


def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _local_encode(texts: list[str], model_name: str, batch_size: int) -> np.ndarray:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Local embeddings require sentence-transformers. Install with: "
            "pip install -e 'ml[embeddings]'"
        ) from exc

    log.info("Loading local embedding model %s", model_name)
    device = os.getenv("RECROS_EMBEDDING_DEVICE", "cpu")
    log.info("Embedding device=%s", device)
    model = SentenceTransformer(model_name, device=device)
    vectors: list[np.ndarray] = []
    for batch in _chunks(texts, batch_size):
        vectors.append(
            np.asarray(
                model.encode(
                    batch,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                ),
                dtype=np.float32,
            )
        )
    return normalize(np.vstack(vectors)) if vectors else np.empty((0, 0), dtype=np.float32)


def _openai_encode(texts: list[str], model_name: str, batch_size: int) -> np.ndarray:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for provider=openai")
    endpoint = os.getenv("OPENAI_EMBEDDINGS_URL", "https://api.openai.com/v1/embeddings")
    vectors: list[np.ndarray] = []
    for batch in _chunks(texts, batch_size):
        payload = json.dumps({"model": model_name, "input": batch, "encoding_format": "float"}).encode()
        request = urllib.request.Request(
            endpoint,
            data=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    body = json.loads(response.read().decode())
                ordered = sorted(body["data"], key=lambda row: int(row["index"]))
                vectors.append(np.asarray([row["embedding"] for row in ordered], dtype=np.float32))
                break
            except (urllib.error.HTTPError, urllib.error.URLError) as exc:
                if attempt == 3:
                    raise RuntimeError(f"Embedding provider failed after retries: {exc}") from exc
                time.sleep(2**attempt)
    return normalize(np.vstack(vectors)) if vectors else np.empty((0, 0), dtype=np.float32)


def encode_texts(
    texts: list[str],
    provider: str = "local",
    model_name: str | None = None,
    batch_size: int = 64,
) -> tuple[np.ndarray, str]:
    provider = provider.strip().lower()
    if provider == "local":
        model = model_name or DEFAULT_LOCAL_MODEL
        return _local_encode(texts, model, batch_size), model
    if provider == "openai":
        model = model_name or DEFAULT_OPENAI_MODEL
        return _openai_encode(texts, model, batch_size), model
    raise ValueError("embedding provider must be local or openai")


def content_hash(texts: list[str]) -> str:
    digest = hashlib.sha256()
    for text in texts:
        digest.update(text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
