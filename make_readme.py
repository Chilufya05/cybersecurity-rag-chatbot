"""Writes README.md, config/config.json and evaluation/evaluation_report.md from your REAL results.

Run AFTER: ingest.py, evaluate.py (and after you filled evaluation/review_sheet.csv).
Run:  python make_readme.py
Then open README.md and check the lines marked  <<< CHECK
"""
import csv
import json
import platform
from datetime import date
from pathlib import Path

AUTHOR = "Chilufya Mwansa"      # <<< CHECK: your name
SUBJECT = "Cybersecurity"
RAM = "24 GB"                   # <<< CHECK: your laptop RAM


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def review_counts():
    path = Path("evaluation/review_sheet.csv")
    if not path.exists():
        return 0, 0, 0, 0
    a_yes = a_no = c_yes = c_no = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))[1:]
    for r in rows:
        if len(r) < 8:
            continue
        a, c = r[6].strip().lower(), r[7].strip().lower()
        a_yes += a == "yes"
        a_no += a == "no"
        c_yes += c == "yes"
        c_no += c == "no"
    return a_yes, a_no, c_yes, c_no


def main():
    manifest = load("data/book_manifest.json")
    ingest_report = load("data/ingest_report.json")
    report = load("evaluation/report.json")
    overall = report["overall"]
    group_id = manifest[0]["book_id"].split("_BOOK_")[0]
    total_pages = sum(b["pages"] for b in ingest_report)
    empty_pages = sum(b["empty_pages"] for b in ingest_report)
    passages = sum(b["passages"] for b in ingest_report)
    failed = [b["file"] for b in ingest_report if b["status"] != "processed"]
    missing_authors = sum(1 for b in manifest if not b["author"].strip())
    a_yes, a_no, c_yes, c_no = review_counts()
    reviewed = a_yes + a_no
    correctness = f"{round(100 * a_yes / reviewed, 1)}% ({a_yes} of {reviewed} reviewed answers)" if reviewed \
        else "NOT YET REVIEWED (fill evaluation/review_sheet.csv)"
    cite_rev = f"{round(100 * c_yes / (c_yes + c_no), 1)}% ({c_yes} of {c_yes + c_no} reviewed)" if (c_yes + c_no) \
        else "NOT YET REVIEWED"

    config = {
        "group_id": group_id, "subject": SUBJECT,
        "retriever": "BM25 (pure Python, no model download)",
        "bm25": {"k1": 1.5, "b": 0.75}, "embedding_model": None,
        "embedding_note": "Embedding model download failed repeatedly on the available connection; "
                          "build_index.py (sentence-transformers all-MiniLM-L6-v2 + FAISS) is included as an optional experiment.",
        "chunking": {"max_chars": 1000, "never_crosses_page": True},
        "top_k": 5, "abstention": {"min_bm25_score": 3.0, "min_keyword_coverage": 0.5},
        "generation": "optional OpenAI-compatible API via LLM_API_KEY / LLM_BASE_URL / LLM_MODEL environment variables; "
                      "without a key the chatbot runs in evidence mode",
        "python": platform.python_version(),
    }
    Path("config").mkdir(exist_ok=True)
    Path("config/config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    readme = f"""# Book-Grounded Cybersecurity Chatbot

**Group ID:** {group_id}   (<<< CHECK: replace with your real group ID if you were given one)
**Subject:** {SUBJECT}
**Team roles:** {AUTHOR} (individual project): all design, code, evaluation and documentation.

## What it does
Answers cybersecurity questions using only {len(manifest)} books. It retrieves relevant passages first, answers
from them, shows the book and page for every answer, and says so when the books do not contain enough evidence.

## Features
- Reads {len(manifest)} PDF books and keeps title, edition, book ID and page number on every passage.
- {passages:,} searchable passages; a passage never crosses a page, so citations stay exact.
- BM25 retrieval with the common `retrieve(question, top_k)` interface.
- Answers in the common format: `answer`, `sources` (book_id, page, chunk_id), `insufficient_evidence`.
- Refuses questions the books cannot answer; invalid citation numbers are removed.
- Two modes: **evidence mode** (no key needed) and **AI mode** (optional API key).
- Simple web page (`app.py`) and a terminal chat (`chatbot.py`).

## Setup and run (Windows)
1. Install Python 3 and run `pip install -r requirements.txt`.
2. Put the PDFs in a folder called `books` (not included: copyright).
3. Build the data, in this order:
   - `python make_manifest.py`   then fill in title/author/edition in `data/book_manifest.json`
   - `python ingest.py`          creates `data/passages.jsonl` (rebuilds the index from permitted sources)
4. Chat: `python chatbot.py`   or the web page: `python app.py` then open http://localhost:8000
5. Optional AI mode (PowerShell): `$env:LLM_API_KEY="your-key"` before running. Never save keys in files or Git.
6. Evaluate: `python make_questions.py`, `python evaluate.py`; tests: `python -m unittest discover tests -v`

## Minimum run configuration
Windows 10 laptop, {RAM} RAM, Python {platform.python_version()}, about 1 GB free disk, no GPU. No internet is needed
for evidence mode. AI mode needs internet for the hosted API (cost, privacy and availability depend on that provider).

## Book manifest
{len(manifest)} books listed in `data/book_manifest.json` ({total_pages:,} pages). Failed books: {failed or 'none'}.
Books with no author filled in: {missing_authors}. Empty/near-empty pages skipped: {empty_pages}.

## Evaluation (actual results; details in `evaluation/evaluation_report.md`)
| Measure | Result |
|---|---|
| Retrieval Recall@5 | {overall['retrieval_recall_at_5_percent']}% on {overall['answerable_questions']} answerable questions |
| Citations resolve to a stored passage | {overall['citations_resolve_percent']}% |
| Correct refusals on no-answer questions | {overall['correct_abstentions_percent']}% of {overall['no_answer_questions']} |
| Answer correctness (human review) | {correctness} |
| Average response time | {overall['avg_seconds']} s |

## Known limitations
- **Retriever:** BM25 keyword search is used instead of the recommended embedding model + FAISS, because the model
  download repeatedly failed on the available internet connection. It matches words, not meaning, so a question
  phrased very differently from the book can be missed. `build_index.py` (embeddings + FAISS) is included as an
  untested optional experiment.
- **Evaluation questions** were generated automatically from passages, which favours keyword search, so Recall@5 is
  probably higher than it would be for natural human questions.
- Evidence mode shows passages instead of writing a new answer. AI mode depends on an external service.
- Text extraction can include page headers, and tables or equations may lose their layout.
- Books and extracted text are not included in the submission because of copyright.
"""
    Path("README.md").write_text(readme, encoding="utf-8")

    fails = [r for r in report["per_question"] if r["type"] != "no-answer" and not r["retrieval_hit_at_5"]]
    wrong_abstain = [r["id"] for r in report["per_question"] if r["type"] != "no-answer" and r["abstained"]]
    wrong_answer = [r["id"] for r in report["per_question"] if r["type"] == "no-answer" and not r["abstained"]]
    splits = "\n".join(f"| {s} | {v['questions']} | {v['retrieval_recall_at_5_percent']}% | {v['correct_abstentions_percent']}% |"
                       for s, v in report["by_split"].items())
    ev = f"""# Evaluation report
Date: {date.today().isoformat()}   Group: {group_id}   Subject: {SUBJECT}

## Test conditions
Windows 10 laptop, {RAM} RAM, Python {platform.python_version()}. Retriever: BM25 (k1=1.5, b=0.75), top_k=5.
{report['passages_indexed']:,} passages from {len(manifest)} books. Questions: `data/evaluation_questions.json`
(validation/test split labels included; settings were tuned on validation questions only).

## Results
| Measure | Result |
|---|---|
| Books processed | {len(manifest) - len(failed)} of {len(manifest)} |
| Pages / empty pages | {total_pages:,} / {empty_pages} |
| Retrieval Recall@5 | {overall['retrieval_recall_at_5_percent']}% (target 80%) |
| Citations resolve to stored passage | {overall['citations_resolve_percent']}% (target 100%) |
| Citation supports expected page | {overall['citation_supports_expected_page_percent']}% |
| Correct abstention on no-answer questions | {overall['correct_abstentions_percent']}% ({overall['no_answer_questions']} questions) |
| Wrongly refused answerable questions | {overall['wrongly_abstained_on_answerable']} |
| Answer correctness (human review) | {correctness} |
| Citation correctness (human review) | {cite_rev} |
| Average / max response time | {overall['avg_seconds']} s / {overall['max_seconds']} s |
| Peak Python memory (approx.) | {report['peak_python_memory_mb_approx']} MB |

### By split
| Split | Questions | Recall@5 | Correct abstentions |
|---|---|---|---|
{splits}

## Failures and error analysis
- Questions where the expected page was not in the top 5: {', '.join(r['id'] for r in fails) or 'none'}
- Answerable questions the chatbot refused: {', '.join(wrong_abstain) or 'none'}
- No-answer questions the chatbot answered anyway: {', '.join(wrong_answer) or 'none'}
- Likely causes: the question words differ from the book's words (BM25 matches words, not meaning); the same
  topic appears on several pages; extraction merged headers or tables into the passage.

## Limitations
Questions were auto-generated from passages, so retrieval results are optimistic. Answer correctness depends on
the manual review of `evaluation/review_sheet.csv`; unreviewed rows are not counted. Memory is Python-only
(tracemalloc), not total process memory.
"""
    Path("evaluation/evaluation_report.md").write_text(ev, encoding="utf-8")
    print("Wrote README.md, config/config.json, evaluation/evaluation_report.md")
    print("Now open README.md and fix the lines marked <<< CHECK")


if __name__ == "__main__":
    main()
