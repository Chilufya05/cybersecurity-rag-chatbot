"""Builds data/evaluation_questions.json automatically (draft, for you to review).

Run:  python make_questions.py

How it works: picks passages from your books (a fixed random sample), and makes a
keyword question from the most distinctive words in each one. The correct book and
page are known, so retrieval can be measured. It also adds 8 questions your books
cannot answer, to test the "not enough evidence" behaviour.
Honest limitation: these questions are auto-generated from the passages, so they
favour keyword search. Rewrite a few by hand into natural questions if you can.
"""
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

from retrieve import tokenize

PASSAGES = Path("data/passages.jsonl")
OUT = Path("data/evaluation_questions.json")
PER_BOOK = 3
TOTAL = 40
SEED = 7

NO_ANSWER = [
    "What is the recipe for a chocolate cake",
    "Who won the 2018 FIFA World Cup",
    "How do I train a dog to sit",
    "What is the capital city of Australia",
    "How many calories are in an apple",
    "Explain the plot of Romeo and Juliet",
    "What is the best way to grow tomatoes",
    "How do airplanes stay in the air",
]


def prose(text):
    letters = sum(c.isalpha() for c in text)
    return len(text) >= 500 and letters / len(text) > 0.75 and "...." not in text


def main():
    passages, df = [], Counter()
    with PASSAGES.open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            terms = set(tokenize(p["text"]))
            df.update(terms)
            passages.append(p)
    n = len(passages)

    by_book = defaultdict(list)
    for p in passages:
        if prose(p["text"]):
            by_book[p["book_id"]].append(p)
    rng = random.Random(SEED)
    chosen = []
    for book in sorted(by_book):
        chosen += rng.sample(by_book[book], min(PER_BOOK, len(by_book[book])))
    rng.shuffle(chosen)
    chosen = chosen[:TOTAL]

    questions = []
    for i, p in enumerate(chosen, start=1):
        tf = Counter(t for t in tokenize(p["text"]) if len(t) >= 4 and not t.isdigit())
        ranked = sorted(tf, key=lambda t: tf[t] * math.log(n / df[t]), reverse=True)[:4]
        questions.append({
            "id": f"Q{i:02d}",
            "question": "What do the books say about " + ", ".join(ranked[:-1]) + " and " + ranked[-1] + "?",
            "type": "factual",
            "expected_book_id": p["book_id"],
            "expected_pages": [p["page"]],
            "reference_answer": p["text"][:250].replace("\n", " "),
            "split": "validation" if i % 2 == 0 else "test",
            "review_status": "auto-generated, pending human review",
        })
    for j, q in enumerate(NO_ANSWER, start=len(questions) + 1):
        questions.append({
            "id": f"Q{j:02d}", "question": q, "type": "no-answer",
            "split": "validation" if j % 2 == 0 else "test",
            "review_status": "written by author",
        })
    OUT.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(questions)} questions ({len(chosen)} answerable, {len(NO_ANSWER)} no-answer) to {OUT}")


if __name__ == "__main__":
    main()
