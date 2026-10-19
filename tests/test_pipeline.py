"""Automated tests. Run from the project folder:  python -m unittest discover tests -v"""
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import chatbot  # noqa: E402
import ingest  # noqa: E402
from retrieve import retrieve, _load  # noqa: E402

REQUIRED_PASSAGE_FIELDS = {"group_id", "subject", "book_id", "title", "page", "chunk_id", "text", "edition"}


class TestIngestion(unittest.TestCase):
    def test_manifest_has_at_least_15_books_with_title(self):
        manifest = json.loads(Path("data/book_manifest.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(manifest), 15)
        for book in manifest:
            self.assertTrue(book["title"].strip())
            self.assertNotEqual(book["processing_status"].split(":")[0], "failed")

    def test_passages_have_required_fields_and_unique_ids(self):
        ids = set()
        with Path("data/passages.jsonl").open(encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                self.assertTrue(REQUIRED_PASSAGE_FIELDS <= set(p))
                self.assertGreaterEqual(p["page"], 1)
                self.assertNotIn(p["chunk_id"], ids)
                ids.add(p["chunk_id"])
        self.assertGreater(len(ids), 0)

    def test_chunking_respects_size_limit(self):
        text = ("Firewalls filter network traffic. " * 80).strip()
        for piece in ingest.split_page(text):
            self.assertLessEqual(len(piece), ingest.MAX_CHARS + ingest.MIN_CHARS)

    def test_clean_joins_hyphenated_words(self):
        self.assertIn("security", ingest.clean("secu-\nrity"))


class TestRetrieval(unittest.TestCase):
    def test_retrieve_returns_required_fields_and_respects_top_k(self):
        passages = _load()["passages"]
        word = passages[0]["text"].split()[5]
        results = retrieve(word, top_k=3)
        self.assertLessEqual(len(results), 3)
        for r in results:
            self.assertTrue({"text", "score", "book_id", "title", "page", "chunk_id"} <= set(r))

    def test_results_sorted_by_score(self):
        text = _load()["passages"][0]["text"]
        scores = [r["score"] for r in retrieve(text[:200], top_k=5)]
        self.assertEqual(scores, sorted(scores, reverse=True))


class TestAnswers(unittest.TestCase):
    def test_answer_format(self):
        text = _load()["passages"][0]["text"]
        result = chatbot.answer(text[:150])
        self.assertEqual(set(result), {"answer", "sources", "insufficient_evidence"})
        self.assertIsInstance(result["sources"], list)

    def test_every_citation_resolves_to_a_stored_passage(self):
        known = {p["chunk_id"] for p in _load()["passages"]}
        for p in _load()["passages"][:20]:
            for s in chatbot.answer(p["text"][:150])["sources"]:
                self.assertIn(s["chunk_id"], known)

    def test_off_topic_question_is_refused(self):
        result = chatbot.answer("How do I bake a chocolate cake")
        self.assertTrue(result["insufficient_evidence"])
        self.assertEqual(result["sources"], [])

    def test_gibberish_is_refused(self):
        self.assertTrue(chatbot.answer("zzzzqqqq xxyyzz")["insufficient_evidence"])

    def test_fake_citation_numbers_are_removed(self):
        cleaned = chatbot.remove_fake_citations("Fact [1] and fake [9].", [{}, {}])
        self.assertIn("[1]", cleaned)
        self.assertNotIn("[9]", cleaned)


if __name__ == "__main__":
    unittest.main()
