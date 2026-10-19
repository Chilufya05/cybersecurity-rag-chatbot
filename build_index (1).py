"""Step 6: turn every passage into an embedding and build a search index.

Run:  python build_index.py
Needs: data/passages.jsonl (made by ingest.py)
Output: data/index.faiss        the search index
        data/index_config.json  model name, revision and settings (for your report)
The first run downloads the embedding model (about 90 MB) so it needs internet.
"""
import json
import time
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

PASSAGES = Path("data/passages.jsonl")
INDEX_FILE = Path("data/index.faiss")
CONFIG_FILE = Path("data/index_config.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64


def main():
    if not PASSAGES.exists():
        print("Run ingest.py first.")
        return

    texts = []
    with PASSAGES.open(encoding="utf-8") as f:
        for line in f:
            texts.append(json.loads(line)["text"])
    print(f"Loaded {len(texts)} passages")

    print(f"Loading model {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    revision = getattr(model[0].auto_model.config, "_commit_hash", None)

    print("Creating embeddings (this takes a few minutes) ...")
    start = time.time()
    vectors = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,   # so inner product = cosine similarity
        convert_to_numpy=True,
    ).astype("float32")
    seconds = round(time.time() - start, 1)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(INDEX_FILE))

    config = {
        "embedding_model": MODEL_NAME,
        "model_revision": revision,
        "embedding_dimension": int(vectors.shape[1]),
        "normalized": True,
        "index_type": "faiss IndexFlatIP (exact cosine search)",
        "passages_indexed": int(index.ntotal),
        "max_passage_chars": 1000,
        "embedding_seconds": seconds,
    }
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"\nIndexed {index.ntotal} passages in {seconds} seconds")
    print(f"Saved {INDEX_FILE} and {CONFIG_FILE}")


if __name__ == "__main__":
    main()
