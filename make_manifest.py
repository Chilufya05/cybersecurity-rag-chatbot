"""Step 3: build the book manifest from the PDFs in the 'books' folder.

Run:  python make_manifest.py
Output: data/book_manifest.json  (open it and fill in any empty fields by hand)
"""
import json
import re
from pathlib import Path

import pymupdf  # installed with: pip install pymupdf

GROUP_ID = "G000"          # <- change to your real group ID
SUBJECT = "Cybersecurity"
BOOKS_DIR = Path("books")
OUT_FILE = Path("data/book_manifest.json")
SAMPLE_PAGES = 10          # pages checked to decide text vs scanned
MIN_CHARS_PER_PAGE = 200   # below this on average = probably scanned


def sample_indexes(n_pages):
    """Pick up to SAMPLE_PAGES pages spread through the book."""
    if n_pages <= SAMPLE_PAGES:
        return list(range(n_pages))
    step = n_pages / SAMPLE_PAGES
    return [int(i * step) for i in range(SAMPLE_PAGES)]


def guess_year(text):
    m = re.search(r"(19|20)\d{2}", text or "")
    return int(m.group(0)) if m else None


def main():
    pdfs = sorted(BOOKS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in '{BOOKS_DIR}'. Put your books there first.")
        return

    manifest = []
    for n, pdf in enumerate(pdfs, start=1):
        entry = {
            "book_id": f"{GROUP_ID}_BOOK_{n:03d}",
            "file": pdf.name,
            "title": "",
            "author": "",
            "edition": "",
            "publisher": "",
            "year": None,
            "isbn": "",
            "subject": SUBJECT,
            "source_type": "",
            "pages": 0,
            "permission_status": "personal copy, processed locally only, not redistributed",
            "processing_status": "pending",
        }
        try:
            doc = pymupdf.open(pdf)
            meta = doc.metadata or {}
            entry["title"] = (meta.get("title") or "").strip() or pdf.stem
            entry["author"] = (meta.get("author") or "").strip()
            entry["year"] = guess_year(meta.get("creationDate", "")[2:6])
            entry["pages"] = doc.page_count

            idx = sample_indexes(doc.page_count)
            chars = [len(doc[i].get_text().strip()) for i in idx]
            avg = sum(chars) / max(len(chars), 1)
            if avg >= MIN_CHARS_PER_PAGE:
                entry["source_type"] = "PDF text"
                entry["processing_status"] = "pending"
            else:
                entry["source_type"] = "scanned PDF"
                entry["processing_status"] = "needs OCR"
            doc.close()
        except Exception as err:  # unreadable / password-protected / damaged
            entry["source_type"] = "unreadable"
            entry["processing_status"] = f"failed: {err}"
        manifest.append(entry)

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nFound {len(manifest)} books\n")
    for e in manifest:
        print(f"{e['book_id']}  {e['pages']:>5} pages  {e['source_type']:<12} {e['file']}")
    if len(manifest) < 15:
        print(f"\nWARNING: the brief needs at least 15 books, you have {len(manifest)}.")
    print(f"\nSaved to {OUT_FILE}. Open it and fill in author, edition, publisher, year and ISBN.")


if __name__ == "__main__":
    main()
