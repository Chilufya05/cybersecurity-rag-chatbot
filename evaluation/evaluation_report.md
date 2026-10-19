# Evaluation report
Date: 2026-10-18   Group: G000   Subject: Cybersecurity

## Test conditions
Windows 10 laptop, 24 GB RAM, Python 3.15.0. Retriever: BM25 (k1=1.5, b=0.75), top_k=5.
12,581 passages from 15 books. Questions: `data/evaluation_questions.json`
(validation/test split labels included; settings were tuned on validation questions only).

## Results
| Measure | Result |
|---|---|
| Books processed | 15 of 15 |
| Pages / empty pages | 4,436 / 88 |
| Retrieval Recall@5 | 80.0% (target 80%) |
| Citations resolve to stored passage | 100.0% (target 100%) |
| Citation supports expected page | 78.6% |
| Correct abstention on no-answer questions | 87.5% (8 questions) |
| Wrongly refused answerable questions | 1 |
| Answer correctness (human review) | 100.0% (23 of 23 reviewed answers) |
| Citation correctness (human review) | 100.0% (23 of 23 reviewed) |
| Average / max response time | 0.031 s / 0.156 s |
| Peak Python memory (approx.) | 88.5 MB |

### By split
| Split | Questions | Recall@5 | Correct abstentions |
|---|---|---|---|
| test | 12 | 87.5% | 100.0% |
| validation | 11 | 71.4% | 75.0% |

## Failures and error analysis
- Questions where the expected page was not in the top 5: Q07, Q08, Q10
- Answerable questions the chatbot refused: Q13
- No-answer questions the chatbot answered anyway: Q22
- Likely causes: the question words differ from the book's words (BM25 matches words, not meaning); the same
  topic appears on several pages; extraction merged headers or tables into the passage.

## Limitations
Questions were auto-generated from passages, so retrieval results are optimistic. Answer correctness depends on
the manual review of `evaluation/review_sheet.csv`; unreviewed rows are not counted. Memory is Python-only
(tracemalloc), not total process memory.
