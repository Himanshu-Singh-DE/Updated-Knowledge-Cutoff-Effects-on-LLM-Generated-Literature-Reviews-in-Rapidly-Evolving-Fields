# Baseline validation report (Gate G2)

Baseline: **Okapi BM25** over title+abstract. Lucene/Anserini idf = log(1 + (N − n + 0.5)/(n + 0.5)), k1 = 0.9, b = 0.4, tokenizer `[a-z0-9]+`
(the same tokenizer as the AI starter code). Implementation: `src/retrieval.py` (sparse matrix). Validation script: `scripts/validate_baseline.py` → `results/logs/03_baseline_validation.log`.

## VERIFIED
| Check | Result | Evidence |
|---|---|---|
| Toy corpus (3 docs): sparse BM25 = independent loop = hand computation | d1 = 0.493374 in all three | log 03 §1 |
| Full corpus (61,877 docs): sparse vs loop on 3 queries | max abs diff 3.55e-15; same top-1 | log 03 §2 |
| Known-item test, 200 random titles as queries (seed 2026) | rank-1: 194/200; top-10: 200/200 | log 03 §3 |
| Decay with h = ∞ reproduces BM25 | top-100 identical for all 54 queries | session check (also logs/09) |
| Decay direction | toy: 2025 doc outranks 2020 doc at h = 12 | log 03 §1 |
| Date filter keeps only docs ≥ T | toy: returns only d3 | log 03 §1 |
| Metric code vs hand computation | P = 0.5, R = 2/3, R_post = 0.5, nDCG = 0.703918 | log 03 §4 |
| Metric code vs AI starter evaluator (real BM25 run, k = 20, 54 queries) | max diff ≤ 9.0e-17 for P, recall, post-recall, nDCG | logs/06 |
| Determinism | re-run gives identical top-100 (logs/09); fresh clone gives identical results (logs/12) | logs/09, logs/12 |
| Label spot-check | 20 random matches printed; titles on-topic for their lists | log 03 §5 |

## UNCERTAIN
* **Not a numerical reproduction of a published run.** The baseline uses Anserini's default parameters but our own code. No published BM25 numbers exist for this testbed, so validation is by independent re-implementation, hand computation and known-item behaviour.
* Label completeness: the curated lists are incomplete and lag the newest papers (paper §4.5).
* 698 papers have year-only dates (set to 1 July).

## NEEDS CORRECTION (resolved)
| Issue | Resolution |
|---|---|
| Starter `environment_test.py` fails: `ModuleNotFoundError: rank_bm25` (logs/01); installs are blocked | Re-implemented BM25 and validated it (above). Deviation: rank_bm25's defaults (k1 = 1.5, b = 0.75, epsilon-floored idf) are **not** used. |
| Starter `evaluate.py` raises `4959 ranked query-paper pairs lack relevance labels` (logs/05) | Unjudged = non-relevant convention; the starter was run with explicit zero labels for cross-checking (logs/06). |

## Acceptable adaptations vs changes that would invalidate comparison
* Acceptable: the same tokenizer, corpus and candidate pool for every method; the decay applied only to the BM25 top-1000.
* Would invalidate (avoided): tuning h on test queries; different corpora per method; labels used during ranking.
