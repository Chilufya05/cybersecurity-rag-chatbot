"""Step 6/7 (no-download version): search your books with BM25.

BM25 is a classic, well-tested keyword-ranking method (used inside search engines).
It needs NO extra libraries and NO model downloads, so it works on any connection.

Try it:   python retrieve.py
Use it in other code:   from retrieve import retrieve
"""
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

PASSAGES = Path("data/passages.jsonl")

K1 = 1.5     # how much repeated words count
B = 0.75     # how much passage length matters

STOPWORDS = set("""a an and are as at be been but by can could did do does for from had has have how
i if in into is it its may might of on or our shall should so such than that the their them then there
these they this those to was we were what when where which while who whom why will with would you your
about also any each more most other some""".split())

_state = {}


def tokenize(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOPWORDS and len(w) > 1]


def _load():
    """Build the search index in memory the first time it is needed (a few seconds)."""
    if _state:
        return _state
    passages, postings, lengths = [], defaultdict(list), []
    with PASSAGES.open(encoding="utf-8") as f:
        for i, line in enumerate(f):
            p = json.loads(line)
            passages.append(p)
            tokens = tokenize(p["text"])
            lengths.append(len(tokens))
            for term, count in Counter(tokens).items():
                postings[term].append((i, count))
    n = len(passages)
    _state.update({
        "passages": passages,
        "postings": postings,
        "lengths": lengths,
        "avg_len": sum(lengths) / max(n, 1),
        "n": n,
    })
    return _state


def retrieve(question: str, top_k: int = 5) -> list:
    """Return passages with text, score, book_id, title, page, and chunk_id."""
    s = _load()
    scores = defaultdict(float)
    for term in set(tokenize(question)):
        plist = s["postings"].get(term)
        if not plist:
            continue
        df = len(plist)
        idf = math.log(1 + (s["n"] - df + 0.5) / (df + 0.5))
        for i, tf in plist:
            norm = tf + K1 * (1 - B + B * s["lengths"][i] / s["avg_len"])
            scores[i] += idf * tf * (K1 + 1) / norm
    best = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = []
    for i, score in best:
        p = s["passages"][i]
        results.append({
            "text": p["text"],
            "score": round(score, 3),
            "book_id": p["book_id"],
            "title": p["title"],
            "edition": p["edition"],
            "page": p["page"],
            "chunk_id": p["chunk_id"],
        })
    return results


if __name__ == "__main__":
    print("Ask a question about your books (type 'quit' to stop).")
    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in ("quit", "exit", ""):
            break
        found = retrieve(q)
        if not found:
            print("No matching passages found.")
        for n, r in enumerate(found, start=1):
            print(f"\n[{n}] score {r['score']} | {r['title']} | page {r['page']} | {r['chunk_id']}")
            print("    " + r["text"][:300].replace("\n", " ") + " ...")
