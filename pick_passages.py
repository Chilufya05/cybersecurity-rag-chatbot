"""Step 9a: pick 45 passages (3 from each book) to base your test questions on.

Run:  python pick_passages.py
Output: data/sample_passages.txt   <- send this file to Claude to get your question set
"""
import json
import random
from collections import defaultdict
from pathlib import Path

PASSAGES = Path("data/passages.jsonl")
OUT = Path("data/sample_passages.txt")
PER_BOOK = 3
SEED = 42    # fixed, so you can repeat the same pick


def looks_like_prose(text):
    """Skip tables of contents, indexes and number tables."""
    letters = sum(c.isalpha() for c in text)
    return len(text) >= 500 and letters / len(text) > 0.75 and "...." not in text


def main():
    by_book = defaultdict(list)
    with PASSAGES.open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            if looks_like_prose(p["text"]):
                by_book[p["book_id"]].append(p)

    rng = random.Random(SEED)
    chosen = []
    for book_id in sorted(by_book):
        pool = by_book[book_id]
        chosen += rng.sample(pool, min(PER_BOOK, len(pool)))

    with OUT.open("w", encoding="utf-8") as out:
        for n, p in enumerate(chosen, start=1):
            out.write(f"=== S{n:02d} | {p['book_id']} | {p['title']} | page {p['page']} | {p['chunk_id']} ===\n")
            out.write(p["text"] + "\n\n")
    print(f"Picked {len(chosen)} passages from {len(by_book)} books.")
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
