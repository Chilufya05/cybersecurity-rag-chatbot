# Book-Grounded Cybersecurity Chatbot

**Group ID:** G000   (no group ID assigned, individual submission by Chilufya Mwansa)
**Subject:** Cybersecurity
**Team roles:** Chilufya Mwansa (individual project): all design, code, evaluation and documentation.

## What it does
Answers cybersecurity questions using only 15 books. It retrieves relevant passages first, answers
from them, shows the book and page for every answer, and says so when the books do not contain enough evidence.

## Features
- Reads 15 PDF books and keeps title, edition, book ID and page number on every passage.
- 12,581 searchable passages; a passage never crosses a page, so citations stay exact.
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
Windows 10 laptop, 24 GB RAM, Python 3.15.0, about 1 GB free disk, no GPU. No internet is needed
for evidence mode. AI mode needs internet for the hosted API (cost, privacy and availability depend on that provider).

## Book manifest
15 books listed in `data/book_manifest.json` (4,436 pages). Failed books: none.
Books with no author filled in: 1. Empty/near-empty pages skipped: 88.

## Evaluation (actual results; details in `evaluation/evaluation_report.md`)
| Measure | Result |
|---|---|
| Retrieval Recall@5 | 80.0% on 15 answerable questions |
| Citations resolve to a stored passage | 100.0% |
| Correct refusals on no-answer questions | 87.5% of 8 |
| Answer correctness (human review) | 100.0% (23 of 23 reviewed answers) |
| Average response time | 0.031 s |

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
