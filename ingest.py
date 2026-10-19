"""Step 5: read every book, clean the text, cut it into passages.

Run:  python ingest.py
Needs: data/book_manifest.json (made by make_manifest.py)
Output: data/passages.jsonl      one passage per line, with book + page info
        data/ingest_report.json  per-book stats (pages, empty pages, passages)
"""
import json
import re
from pathlib import Path

import pymupdf

BOOKS_DIR = Path("books")
MANIFEST = Path("data/book_manifest.json")
PASSAGES_OUT = Path("data/passages.jsonl")
REPORT_OUT = Path("data/ingest_report.json")

MAX_CHARS = 1000      # target maximum size of one passage
MIN_CHARS = 200       # a leftover piece smaller than this is joined to the one before
MIN_PAGE_CHARS = 50   # pages with less text than this are counted as empty


def clean(text):
    text = text.replace("­", "")                 # soft hyphens
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)      # join words split across lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_page(text):
    """Cut one page of text into passages of at most MAX_CHARS.
    A passage never crosses a page boundary, so page citations stay exact."""
    paragraphs = [p.replace("\n", " ").strip() for p in re.split(r"\n\s*\n", text)]
    pieces, current = [], ""
    for para in paragraphs:
        if not para:
            continue
        # a very long paragraph is cut at sentence ends
        sentences = re.split(r"(?<=[.!?])\s+", para) if len(para) > MAX_CHARS else [para]
        for s in sentences:
            while len(s) > MAX_CHARS:                  # last resort: hard cut at a space
                cut = s.rfind(" ", 0, MAX_CHARS)
                cut = cut if cut > 0 else MAX_CHARS
                if current:
                    pieces.append(current)
                    current = ""
                pieces.append(s[:cut].strip())
                s = s[cut:].strip()
            if len(current) + len(s) + 1 <= MAX_CHARS:
                current = (current + " " + s).strip()
            else:
                pieces.append(current)
                current = s
    if current:
        pieces.append(current)
    # join a tiny last piece onto the previous one
    if len(pieces) > 1 and len(pieces[-1]) < MIN_CHARS:
        last = pieces.pop()
        pieces[-1] = (pieces[-1] + " " + last).strip()
    return [p for p in pieces if p]


def main():
    if not MANIFEST.exists():
        print("Run make_manifest.py first.")
        return
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    report, total = [], 0

    with PASSAGES_OUT.open("w", encoding="utf-8") as out:
        for book in manifest:
            path = BOOKS_DIR / book["file"]
            group_id = book["book_id"].split("_BOOK_")[0]
            stats = {"book_id": book["book_id"], "file": book["file"],
                     "pages": 0, "empty_pages": 0, "passages": 0, "status": "processed"}
            try:
                doc = pymupdf.open(path)
                stats["pages"] = doc.page_count
                for i, page in enumerate(doc, start=1):   # i = printed PDF page number
                    text = clean(page.get_text())
                    if len(text) < MIN_PAGE_CHARS:
                        stats["empty_pages"] += 1
                        continue
                    for c, piece in enumerate(split_page(text), start=1):
                        record = {
                            "group_id": group_id,
                            "subject": book["subject"],
                            "book_id": book["book_id"],
                            "title": book["title"],
                            "edition": book["edition"],
                            "page": i,
                            "chunk_id": f"{book['book_id']}_P{i}_C{c:02d}",
                            "text": piece,
                        }
                        out.write(json.dumps(record, ensure_ascii=False) + "\n")
                        stats["passages"] += 1
                doc.close()
            except Exception as err:
                stats["status"] = f"failed: {err}"
            total += stats["passages"]
            report.append(stats)
            print(f"{book['book_id']}  {stats['pages']:>4} pages  "
                  f"{stats['empty_pages']:>3} empty  {stats['passages']:>5} passages  {stats['status']}")

    REPORT_OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nTotal passages: {total}")
    print(f"Saved {PASSAGES_OUT} and {REPORT_OUT}")


if __name__ == "__main__":
    main()
