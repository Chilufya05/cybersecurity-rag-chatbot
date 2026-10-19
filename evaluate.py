"""Step 9b: measure how good your chatbot is.

Run:  python evaluate.py
Needs: data/evaluation_questions.json
Output: evaluation/report.json         the numbers for your report
        evaluation/review_sheet.csv    answers for you to mark correct / incorrect by hand
"""
import csv
import json
import time
import tracemalloc
from pathlib import Path

from chatbot import answer
from retrieve import retrieve, _load

QUESTIONS = Path("data/evaluation_questions.json")
OUT_DIR = Path("evaluation")


def pct(a, b):
    return round(100 * a / b, 1) if b else None


def main():
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(exist_ok=True)

    tracemalloc.start()
    state = _load()
    known_chunks = {p["chunk_id"] for p in state["passages"]}

    rows, review = [], []
    for q in questions:
        expected_book = q.get("expected_book_id")
        expected_pages = q.get("expected_pages") or []
        no_answer = q["type"] == "no-answer"

        start = time.time()
        passages = retrieve(q["question"], 5)
        result = answer(q["question"])
        seconds = round(time.time() - start, 3)

        hit = None
        if not no_answer:
            hit = any(p["book_id"] == expected_book and p["page"] in expected_pages for p in passages)
        cited_ok = all(s["chunk_id"] in known_chunks for s in result["sources"])
        cite_supports = None
        if not no_answer and result["sources"]:
            cite_supports = any(s["book_id"] == expected_book and s["page"] in expected_pages
                                for s in result["sources"])

        rows.append({
            "id": q["id"], "split": q.get("split", "test"), "type": q["type"],
            "retrieval_hit_at_5": hit,
            "abstained": result["insufficient_evidence"],
            "citations_resolve": cited_ok,
            "citation_supports": cite_supports,
            "seconds": seconds,
        })
        review.append([q["id"], q["type"], q["question"], q.get("reference_answer", ""),
                       result["answer"].replace("\n", " ")[:600],
                       "; ".join(f"{s['book_id']} p.{s['page']}" for s in result["sources"]),
                       "", ""])

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    def summary(subset):
        ans = [r for r in subset if r["type"] != "no-answer"]
        noans = [r for r in subset if r["type"] == "no-answer"]
        with_sources = [r for r in ans if r["citation_supports"] is not None]
        return {
            "questions": len(subset),
            "answerable_questions": len(ans),
            "retrieval_recall_at_5_percent": pct(sum(r["retrieval_hit_at_5"] for r in ans), len(ans)),
            "citations_resolve_percent": pct(sum(r["citations_resolve"] for r in subset), len(subset)),
            "citation_supports_expected_page_percent":
                pct(sum(r["citation_supports"] for r in with_sources), len(with_sources)),
            "wrongly_abstained_on_answerable": sum(r["abstained"] for r in ans),
            "no_answer_questions": len(noans),
            "correct_abstentions_percent": pct(sum(r["abstained"] for r in noans), len(noans)),
            "avg_seconds": round(sum(r["seconds"] for r in subset) / max(len(subset), 1), 3),
            "max_seconds": max((r["seconds"] for r in subset), default=None),
        }

    report = {
        "overall": summary(rows),
        "by_split": {s: summary([r for r in rows if r["split"] == s])
                     for s in sorted({r["split"] for r in rows})},
        "peak_python_memory_mb_approx": round(peak / 1e6, 1),
        "passages_indexed": state["n"],
        "note": "Answer correctness is human-reviewed: fill the last two columns of review_sheet.csv.",
        "per_question": rows,
    }
    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (OUT_DIR / "review_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "question", "reference_answer", "chatbot_answer", "sources",
                    "answer_correct (yes/no)", "citation_correct (yes/no)"])
        w.writerows(review)

    print(json.dumps(report["overall"], indent=2))
    print("\nSaved evaluation/report.json and evaluation/review_sheet.csv")


if __name__ == "__main__":
    main()
