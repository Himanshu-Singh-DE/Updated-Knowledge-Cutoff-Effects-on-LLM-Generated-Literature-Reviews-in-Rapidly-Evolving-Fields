# AI assistance and provenance log (Prompt 18)

Tools: an AI assistant (Claude) used (a) earlier, to produce the gap matrix (Prompts 01–02) and the planning/starter-code bundle (Prompts 03–14), and (b) in a supervised session on 14 Nov 2026 to implement, run and write up the study. **The author must review, re-run and be able to explain every module before submission.**

| # | Task | AI proposal | Human / verification step | Change | Outcome |
|---|---|---|---|---|---|
| 1 | Pathway choice | Prompts 03–05: BM25 vs recency-aware re-ranker, post-cutoff recall@k | Checked feasibility on CPU, no model weights needed | Adopted (D011) | Executed |
| 2 | Data source | Prompt 06: "build a verified dated corpus" (no source named) | Probed network access: OpenAlex, arXiv, Semantic Scholar and HuggingFace refused by the egress proxy; GitHub reachable via git | Chose ACL Anthology XML plus curated GitHub lists (D013–D014) | Pinned commits |
| 3 | Environment test | Starter `environment_test.py` | **Ran it: failed** (`rank_bm25` missing, logs/01) | Own BM25 plus validation | Real limitation #1 |
| 4 | Evaluator | Starter `evaluate.py` | **Ran it on real rankings: raised ValueError** (logs/05) | Unjudged = non-relevant; cross-check to 1e-16 (logs/06) | Real limitation #2 |
| 5 | Queries | AI drafted 54 topic queries | Written before any retrieval; frozen (configs/queries_spec.json) | – | **Author to review wording** |
| 6 | Protocol freeze | AI wrote configs/experiment.json | Hash recorded before runs (D019) | – | Followed |
| 7 | Unexpected result | Gentle decay (h = 96) halved recall on tuning | Treated as a possible bug; inspected q06 rankings (logs/08) | No bug; mechanism analysis added (post hoc) | Real verification #3 |
| 8 | Ground-truth staleness | Observation from the q01 example | Added coverage-window re-evaluation (post hoc, labelled) | – | Conclusions unchanged |
| 9 | Figures/tables | Generated from CSVs by scripts | Fresh-clone reproduction is byte-identical except latency (logs/12) | – | Verified |
| 10 | Bibliography | AI drafted the BibTeX | 5 IR references checked by web search on 14 Nov 2026; review-derived ones as in the gap matrix | Shortened author lists where unverified | See paper/bib_verification.md |
| 11 | Manuscript | AI drafted all sections from results files | Number macros auto-generated; [TO VERIFY] markers left | – | **Author to revise in own words** |
| 12 | Alignment with the survey | Re-read the full survey PDF; matched template, cross-references and bibliography | Every §/Eq./Fig. number cited in the paper was checked against the survey text | Bridge table rewritten; new §4.7 linking ρ and g | Done |

## Conclusions that depend on human judgment
* Whether the decay's "non-relevant" 2025 papers are truly relevant. This needs manual judging (not done).
* Query wording and whether section-level lists represent coherent topics.
* Interpreting the date filter as a "control" rather than a mitigation.

## What was learned about vibe coding
* Starter code that "looks right" failed on first contact with the real environment, both on dependencies and on evaluation assumptions.
* Running everything early exposed the surprising negative result. The frozen protocol kept it from being tuned away.

## Remaining risks
* The labels are incomplete and time-lagged. All queries and the paper text were AI-drafted. There are no human relevance judgments.
