# Does Recency-Aware Re-ranking Close the Temporal Coverage Gap?

Course: **AI Tools for Research**, post-mid-semester implementation paper.
Author: **Himanshu Singh (MDE_015)**. Earlier survey: *Knowledge Cutoff Effects on LLM-Generated Literature Reviews in Rapidly Evolving Fields: A Survey* (ACM CSUR format).
Pathway: **B, a controlled comparative study** (with a targeted-modification arm: BM25 plus time decay).

## Research question
At the retrieval stage that feeds an LLM review writer, does re-ranking BM25 results by recency raise the fraction of
relevant papers published after a nominal cutoff T = 2023-07-01 that appear in the top 20 (R_post@20, the
retrieval-stage version of the review's temporal coverage ratio) without hurting topical relevance?

## Headline results (held-out test topics; all numbers come from `results/`)
| Method | R_post@20 | ΔR_post@20 vs BM25 [95% CI] | nDCG@20 | ΔnDCG@20 [95% CI] |
|---|---|---|---|---|
| BM25 (baseline) | 0.146 | – | 0.187 | – |
| TF-IDF (baseline 2) | 0.108 | −0.037 [−0.078, −0.001] | 0.165 | −0.022 [−0.058, +0.011] |
| Date filter ≥ T (control) | 0.181 | +0.035 [+0.015, +0.058] | 0.168 | −0.019 [−0.039, −0.001] |
| BM25+Decay, h=12 (post hoc) | 0.046 | −0.099 [−0.135, −0.068] | 0.052 | −0.135 [−0.177, −0.094] |

* The pre-registered tuning step rejected every finite decay half-life (h* = ∞), so H1 is **not supported**. This is a negative result.
* The date filter's gain is below the pre-registered +0.05 threshold. It drops nDCG to 0 on topics with no recent literature.
* Plain BM25 already returns 83% post-cutoff papers in its top 20 (curated relevant sets: 73%; corpus: 52%).
* Link back to the survey's severity model: BM25's post-cutoff recall at depth 20, the survey's ρ (Eq. 4), is 0.146, and ACL output grows at g = 0.157/yr (Eq. 3; the survey's Fig. 5 values lacked a source).
* The curated ground truth lags the newest papers (2025 makes up 23% of the corpus but only 9.8% of the labels). Part of the measured harm of decay is therefore a label-staleness artefact. A coverage-window re-evaluation leaves the conclusions unchanged.

## Repository layout
```
configs/        experiment.json (frozen protocol), queries_spec.json, lists.json (pinned commits)
src/            build_corpus.py, match_lists.py, build_labels.py, retrieval.py, metrics.py
scripts/        fetch_data.sh, run_all.sh, validate_baseline.py, run_retrieval.py, select_h.py,
                evaluate_all.py, analysis_mechanism.py, make_figures.py, make_tables.py
starter_ai_code/  AI-generated starter code from Prompts 08–13, kept unchanged for provenance
data/           documents.csv (corpus), queries.csv, relevance*.csv, query_meta*.csv, list_matches.csv
results/        rankings.csv.gz (top-1000), metrics_by_query.csv, table_*.csv, numbers.json, logs/
paper/          main.tex, references.bib, generated/ (auto tables + number macros), figures/, main.pdf
docs/           research_brief_G1.md
research_decisions.md  baseline_validation.md  ai_assistance_log.md
```

## Reproduce (verified: a fresh copy gives byte-identical results; see results/logs/12_fresh_reproduction.log)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt                 # [TEST REQUIRED] install was not run here; versions were already present
bash scripts/fetch_data.sh ../data_raw          # clones ACL Anthology (sparse data/xml) + 34 lists at pinned commits (~1 min)
bash scripts/run_all.sh ../data_raw             # ~1 min on 2 CPU cores; regenerates data/, results/, paper/generated, paper/figures
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
On Overleaf, upload `paper/` (main.tex, references.bib, generated/, figures/). Overleaf provides `acmart` and its fonts.

* Compute: CPU only, about 1.5 GB RAM; index build takes about 7 s, and each method needs 9–20 ms per query.
* Randomness: retrieval is deterministic (ties broken by paper_id). The list split and bootstrap use seed 2026.
* Only the latency numbers change between runs.

## Data and licences
* ACL Anthology metadata: https://github.com/acl-org/acl-anthology (the Anthology states its content is CC BY 4.0. **[TO VERIFY]** licence wording on the repo at the pinned commit).
* Curated lists: 34 public GitHub repositories (see `configs/lists.json`). Only titles are matched; no list content is redistributed beyond paper IDs and section names in `data/list_matches.csv`. **[TO VERIFY]** each repository's licence before making this repository public.
* No API keys, private data or model weights are used.

## Limitations
This is a retrieval-stage proxy, not an evaluation of generated reviews. The labels are incomplete and time-lagged, the corpus covers ACL venues only, and n = 35 test active topics. See Section 6 of the paper.

## Minimum reproduction checklist for a second student
- [ ] `fetch_data.sh` prints `ok` for 35 repositories
- [ ] `results/logs/03_baseline_validation.log` ends with `ALL BASELINE CHECKS PASSED`
- [ ] `results/selected_h.json` contains `"h_star_months": Infinity`
- [ ] `results/table_main_test.csv`: BM25 R_post = 0.1457, DateFilter R_post = 0.1807
- [ ] `paper/main.pdf` compiles with no undefined references

## Citation
```
Himanshu Singh (MDE_015). Does Recency-Aware Re-ranking Close the Temporal Coverage Gap? A Controlled Retrieval-Stage
Study for LLM-Assisted Literature Reviews. AI Tools for Research course project, 2026.
```
Code licence: MIT **[author to confirm]**.
