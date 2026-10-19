"""Step 8: the chatbot. Retrieve passages -> answer with citations -> abstain if no evidence.

Run in the terminal:   python chatbot.py
Use in other code:     from chatbot import answer

Two modes (chosen automatically):
  * AI mode:        if an API key is set, an AI model writes the answer from the passages.
  * Evidence mode:  no key needed. Shows the best matching passages with citations.
Both modes return the same format as the project brief:
  {"answer": "...", "sources": [{"book_id","page","chunk_id"}], "insufficient_evidence": bool}
"""
import json
import os
import re
import urllib.request

from retrieve import retrieve, tokenize

# ---------- settings you can change ----------
TOP_K = 5
MIN_SCORE = 4.0          # best passage must score at least this (BM25 score)
MIN_COVERAGE = 0.7       # at least this share of the question's keywords must appear in it

# AI mode settings. Set these in the terminal before running (see instructions):
API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
MODEL = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
# ---------------------------------------------

NO_EVIDENCE = "The provided books do not contain enough evidence to answer this question."


def has_enough_evidence(question, passages):
    """Decide whether the retrieved passages are good enough to answer from."""
    if not passages:
        return False
    best = passages[0]
    q_terms = set(tokenize(question))
    if not q_terms:
        return False
    p_terms = set(tokenize(best["text"]))
    coverage = len(q_terms & p_terms) / len(q_terms)
    return best["score"] >= MIN_SCORE and coverage >= MIN_COVERAGE


def to_source(p):
    return {"book_id": p["book_id"], "page": p["page"], "chunk_id": p["chunk_id"]}


def evidence_mode(passages):
    """No AI: show the best passages, each tied to its citation."""
    lines = []
    for n, p in enumerate(passages[:3], start=1):
        text = p["text"].replace("\n", " ")
        lines.append(f"[{n}] {text[:450]}{'...' if len(text) > 450 else ''}  ({p['title']}, p. {p['page']})")
    return "Relevant passages from your books:\n\n" + "\n\n".join(lines), [to_source(p) for p in passages[:3]]


def ask_llm(question, passages):
    """Send the passages + question to an AI model and get back an answer with [n] citations."""
    context = "\n\n".join(f"[{n}] ({p['title']}, page {p['page']})\n{p['text']}"
                          for n, p in enumerate(passages, start=1))
    prompt = (
        "Answer the question using ONLY the numbered passages below. "
        "Cite the passages you use as [1], [2] after each claim. "
        "Do not invent facts or citations. If the passages do not contain the answer, "
        f"reply exactly: {NO_EVIDENCE}\n\nPASSAGES:\n{context}\n\nQUESTION: {question}"
    )
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }).encode()
    req = urllib.request.Request(
        BASE_URL.rstrip("/") + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def remove_fake_citations(text, passages):
    """Delete any [n] that does not point to one of the passages we really gave the AI."""
    return re.sub(r"\s*\[(\d+)\]",
                  lambda m: m.group(0) if 1 <= int(m.group(1)) <= len(passages) else "", text)


def used_sources(text, passages):
    """Keep only citations the AI really used, and only ones that map to a stored passage."""
    nums = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 1 <= int(n) <= len(passages)})
    return [to_source(passages[n - 1]) for n in nums]


def answer(question: str) -> dict:
    passages = retrieve(question, TOP_K)
    if not has_enough_evidence(question, passages):
        return {"answer": NO_EVIDENCE, "sources": [], "insufficient_evidence": True}

    if API_KEY:
        try:
            text = ask_llm(question, passages)
            if text.startswith(NO_EVIDENCE[:40]):
                return {"answer": NO_EVIDENCE, "sources": [], "insufficient_evidence": True}
            text = remove_fake_citations(text, passages)
            sources = used_sources(text, passages)
            if sources:   # every shown citation is a real stored passage
                return {"answer": text, "sources": sources, "insufficient_evidence": False}
        except Exception as err:
            print(f"(AI service unavailable: {err}. Showing evidence mode instead.)")

    text, sources = evidence_mode(passages)
    return {"answer": text, "sources": sources, "insufficient_evidence": False}


if __name__ == "__main__":
    print("AI mode ON" if API_KEY else "Evidence mode (no AI key set)")
    print("Ask a cybersecurity question (type 'quit' to stop).")
    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in ("quit", "exit", ""):
            break
        result = answer(q)
        print("\n" + result["answer"])
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  - {s['book_id']}, page {s['page']}, {s['chunk_id']}")
