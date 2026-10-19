"""Builds data/evaluation_questions.json from YOUR chosen questions.

Run:  python make_my_questions.py
Then read the printed check list: for each question it shows the book text on that page.
If the text does NOT answer the question, edit that line in the MY_QUESTIONS list below.
"""
import json
from pathlib import Path
from retrieve import tokenize

PASSAGES = Path("data/passages.jsonl")
OUT = Path("data/evaluation_questions.json")

# (question, book_id, page, type)
MY_QUESTIONS = [
    ("Why are software safeguards alone not sufficient for security?", "G000_BOOK_001", 12, "reasoning"),
    ("How does subject-to-program and program-to-object binding enforce integrity?", "G000_BOOK_002", 188, "reasoning"),
    ("What is signature dynamics as a biometric?", "G000_BOOK_002", 173, "factual"),
    ("What is the first step in securing endpoints?", "G000_BOOK_003", 53, "factual"),
    ("What techniques increase the security of memory token systems?", "G000_BOOK_004", 197, "factual"),
    ("What real-world examples show the importance of cybersecurity?", "G000_BOOK_005", 16, "factual"),
    ("Why is Python a good choice for cybersecurity?", "G000_BOOK_005", 32, "reasoning"),
    ("What does ALARP mean in risk management?", "G000_BOOK_008", 823, "factual"),
    ("What is the role of international laws in computing and communications?", "G000_BOOK_009", 30, "factual"),
    ("What is shell code in a buffer overflow attack?", "G000_BOOK_010", 148, "factual"),
    ("What are diploma mills?", "G000_BOOK_012", 43, "factual"),
    ("What role does a computer forensic investigator play?", "G000_BOOK_012", 34, "factual"),
    ("What is the Nikto web server scanner used for?", "G000_BOOK_013", 123, "factual"),
    ("How should an organisation handle Advanced Persistent Threats?", "G000_BOOK_013", 38, "reasoning"),
    ("How can software piracy be mitigated during installation?", "G000_BOOK_015", 125, "reasoning"),
]

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


def main():
    by_page = {}
    with PASSAGES.open(encoding="utf-8") as f:
        for line in f:
            p = json.loads(line)
            by_page.setdefault((p["book_id"], p["page"]), []).append(p)

    out, problems = [], 0
    for i, (q, book, page, qtype) in enumerate(MY_QUESTIONS, start=1):
        chunks = by_page.get((book, page))
        if not chunks:
            print(f"!! Q{i:02d}: no text found for {book} page {page} - fix book/page")
            problems += 1
            continue
        qterms = set(tokenize(q))
        best = max(chunks, key=lambda c: len(qterms & set(tokenize(c["text"]))))
        ref = best["text"][:400].replace("\n", " ")
        print(f"\nQ{i:02d} {q}\n    [{book} p{page}] {ref[:300]}")
        out.append({
            "id": f"Q{i:02d}", "question": q, "type": qtype,
            "expected_book_id": book, "expected_pages": [page],
            "reference_answer": ref,
            "split": "validation" if i % 2 == 0 else "test",
            "review_status": "written by author, checked against book text",
        })
    for j, q in enumerate(NO_ANSWER, start=len(out) + 1):
        out.append({"id": f"Q{j:02d}", "question": q, "type": "no-answer",
                    "split": "validation" if j % 2 == 0 else "test",
                    "review_status": "written by author"})
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(out)} questions to {OUT} ({problems} problems)")


if __name__ == "__main__":
    main()
