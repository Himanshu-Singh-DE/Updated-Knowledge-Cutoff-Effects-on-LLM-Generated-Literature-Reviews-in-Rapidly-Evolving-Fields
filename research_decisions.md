# research_decisions.md

Tags: **VERIFIED** (checked in a source or by execution, with evidence path), **INFERRED** (reasoning), **UNKNOWN** (missing evidence).
D001–D010 are carried over from the Prompt 01/02 gap matrix (22 Oct 2026). D011 onward were added during implementation (14 Nov 2026).

| ID | Date | Decision | Reason | Evidence | Status |
|---|---|---|---|---|---|
| D001 | 2026-10-22 | The 25-page review is the scope baseline | Prompt 01 | review PDF | VERIFIED |
| D002 | 2026-10-22 | Numbers quoted from the review are "reported by cited source" | Review reports no experiments | review Tables 2, 6, 7 | VERIFIED |
| D003 | 2026-10-22 | 9 cited sources spot-checked; the rest unchecked | Gap matrix App. A | gap-matrix PDF | VERIFIED (9) |
| D004 | 2026-10-22 | Fix S6.2/S9 wording: Chelli et al. do report recall | Internal inconsistency | JMIR page | VERIFIED |
| D005 | 2026-10-22 | Five candidate gaps CG1–CG5; no novelty claims | Prompt 02 | gap matrix B2 | INFERRED |
| D006 | 2026-10-22 | Provisional ranking CG2 > CG4 > CG1 | Resources unknown | gap matrix B4 | INFERRED |
| D007 | 2026-10-22 | Candidate baseline: refresh Chelli-style replication | S7.6, S8.3 | review | Superseded by D012 |
| D008 | 2026-10-22 | Growth rates g = 0.20/0.35/0.50 are not presented as empirical | No source cited | review S4.2 | VERIFIED; partly resolved by D028 |
| D009 | 2026-10-22 | Five review figures not confirmed | Pages did not load | gap matrix App. A | UNKNOWN (not reused in this paper) |
| D010 | 2026-10-22 | No code or results existed | – | – | VERIFIED (then) |
| D011 | 2026-11-14 | Adopt the Prompts 03–07 plan: pathway B, BM25 vs a recency-aware re-ranker, primary metric post-cutoff recall@k | Feasible on CPU without model weights; tests retrieval-stage part of CG1/CG4 | AI outputs 03–07 | INFERRED → executed |
| D012 | 2026-11-14 | Do not run LLM generation (CG2/D007) | No verified model/API access in the environment; package installs and most hosts blocked | proxy denials in session; logs/01 | VERIFIED constraint |
| D013 | 2026-11-14 | Corpus = ACL Anthology XML 2018–2025 with abstracts, pinned commit f188191 | Only GitHub reachable via git; official, dated, open metadata | configs/lists.json; build_corpus.py output | VERIFIED |
| D014 | 2026-11-14 | Relevance = exact normalised title match of entries in 34 curated GitHub reading lists | Expert lists are the review's K_post proxy; exact match gives high precision | src/match_lists.py; logs/03 §5 | VERIFIED (execution); label completeness UNKNOWN |
| D015 | 2026-11-14 | 54 hand-written topic queries (AI-drafted), ≥ 8 labels each, written before any run | Topic-level queries mirror how a review writer searches | configs/queries_spec.json | VERIFIED; wording needs author review |
| D016 | 2026-11-14 | T = 2023-07-01; robustness at 2022-07-01 and 2024-07-01; t_ref = 2025-12-01 | Mid-window; GPT-4-era anchors | configs/experiment.json | VERIFIED |
| D017 | 2026-11-14 | Split by source list (seed 2026), 30% of lists for tuning | Avoid same-curator leakage | data/query_meta.csv | VERIFIED |
| D018 | 2026-11-14 | BM25 k1 = 0.9, b = 0.4 (Anserini defaults), own sparse implementation | rank_bm25 missing and installs blocked | logs/01, logs/03 | VERIFIED |
| D019 | 2026-11-14 | Freeze selection rule, success threshold (+0.05) and guardrail (−0.02 nDCG) before running | Prevent test-set tuning | configs/experiment.json (sha256 2129ce4d…) | VERIFIED |
| D020 | 2026-11-14 | Unjudged = non-relevant; starter evaluator not used for scoring | Starter refuses unjudged pairs | logs/05, logs/06 | VERIFIED |
| D021 | 2026-11-14 | Selection on tuning returned h* = ∞; report the test results as a negative result | Frozen rule | logs/07, results/selected_h.json | VERIFIED |
| D022 | 2026-11-14 | Investigate the unexpected recall drop under gentle decay as a possible bug | Collapse at h = 96 looked suspicious | logs/08 (no bug; mechanism) | VERIFIED |
| D023 | 2026-11-14 | Protocol change (logged): save rankings to depth 1000 (was 100) for the coverage-window analysis | Need deeper lists after removing papers | logs/09 (top-100 identical) | VERIFIED; post hoc |
| D024 | 2026-11-14 | Add post-hoc analyses: decay grid on test, coverage-window evaluation, mechanism, velocity correlation | Explain the negative result | evaluate_all.py, analysis_mechanism.py | VERIFIED; labelled post hoc in the paper |
| D025 | 2026-11-14 | Paper template: ACM acmsmall (as in the mid-sem review), all numbers via generated macros | Traceability | paper/generated/numbers.tex | VERIFIED |
| D026 | 2026-11-14 | Fresh-copy reproduction from pinned sources | Gate G4 | logs/12 (byte-identical except latency) | VERIFIED |
| D027 | 2026-11-14 | Align the paper with the author's survey (MDE_015): same CSUR acmsmall format, author Himanshu Singh, cross-references to the survey's §/Eq./Fig. numbers, bibliography metadata copied from the survey's verified reference list | The survey was supplied as the evidence base | survey PDF; paper/references.bib | VERIFIED |
| D028 | 2026-11-14 | Post hoc: estimate the survey's g (Eq. 3) from ACL output 2018–2025 → g = 0.157/yr (R² 0.96) | The survey's Fig. 5 used unsourced g values | scripts/analysis_growth.py; logs/13 | VERIFIED (descriptive) |
| D029 | 2026-11-14 | Report BM25 R_post@k as the survey's ρ (Eq. 4): 0.146 (k=20), 0.345 (k=100) | The survey called ρ measurable but gave no value | results/growth.json | VERIFIED for this testbed only |

## Open next actions (author)
1. Read and own every script; re-run `scripts/run_all.sh`.
2. Review the 54 query texts and a sample of labels; record agreement.
3. Manually judge the top-20 of 3–5 topics under BM25 and Decay(h=12) to measure label staleness. This is the paper's [TO VERIFY] item and its follow-up #1.
4. Fill in the institute name and licence (author and enrollment number are now set from the survey file name; confirm them).
5. Verify the bib items marked in `paper/bib_verification.md`.
