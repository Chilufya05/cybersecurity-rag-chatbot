"""Builds submission.zip with everything the brief asks for, WITHOUT the books or extracted text.

Run:  python package_submission.py
"""
import zipfile
from pathlib import Path

FILES = [
    "README.md", "requirements.txt",
    "make_manifest.py", "ingest.py", "retrieve.py", "chatbot.py", "app.py",
    "make_my_questions.py", "review.py", "make_questions.py", "evaluate.py", "make_readme.py", "pick_passages.py", "build_index.py",
    "config/config.json",
    "data/book_manifest.json", "data/evaluation_questions.json", "data/ingest_report.json",
    "tests/test_pipeline.py",
    "evaluation/report.json", "evaluation/review_sheet.csv", "evaluation/evaluation_report.md",
]
OPTIONAL_EXTRA = ["demo.mp4"]   # put your demo video next to this script if small enough

missing = []
with zipfile.ZipFile("submission.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name in FILES + OPTIONAL_EXTRA:
        p = Path(name)
        if p.exists():
            z.write(p, name)
        elif name not in OPTIONAL_EXTRA:
            missing.append(name)
print("Created submission.zip (no books, no passages.jsonl, no keys).")
if missing:
    print("MISSING (run the earlier steps first):", ", ".join(missing))
