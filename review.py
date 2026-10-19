"""Review the chatbot's answers in the terminal (no Excel needed).

Run:  python review.py
For each question it shows the reference answer, the chatbot's answer and its sources.
You type  y  (yes) or  n  (no).  Type  q  to stop and save. Run it again to continue
where you stopped.
"""
import csv
from pathlib import Path

SHEET = Path("evaluation/review_sheet.csv")


def ask(prompt):
    while True:
        a = input(prompt).strip().lower()
        if a in ("y", "n", "q"):
            return a
        print("   type y, n or q")


def main():
    with SHEET.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    AC = next(k for k in fields if k.startswith("answer_correct"))
    CC = next(k for k in fields if k.startswith("citation_correct"))
    todo = [r for r in rows if not r[AC].strip()]
    done = len(rows) - len(todo)
    print(f"{done} rows already reviewed, {len(todo)} left. Aim for at least 20 in total.\n")

    for r in todo:
        print("=" * 70)
        print(f"{r['id']}  ({r['type']})")
        print("QUESTION  :", r["question"])
        print("REFERENCE :", r["reference_answer"][:300] or "(none - should refuse)")
        print("CHATBOT   :", r["chatbot_answer"][:400])
        print("SOURCES   :", r["sources"])
        if r["type"] == "no-answer":
            a = ask("Did it correctly refuse (say not enough evidence)? y/n/q: ")
            if a == "q":
                break
            r[AC] = r[CC] = "yes" if a == "y" else "no"
        else:
            a = ask("Is the ANSWER correct? y/n/q: ")
            if a == "q":
                break
            c = ask("Is the CITATION (book + page) correct? y/n/q: ")
            if c == "q":
                break
            r[AC] = "yes" if a == "y" else "no"
            r[CC] = "yes" if c == "y" else "no"
        with SHEET.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    reviewed = sum(1 for r in rows if r[AC].strip())
    print(f"\nSaved. {reviewed} of {len(rows)} rows reviewed.")


if __name__ == "__main__":
    main()
