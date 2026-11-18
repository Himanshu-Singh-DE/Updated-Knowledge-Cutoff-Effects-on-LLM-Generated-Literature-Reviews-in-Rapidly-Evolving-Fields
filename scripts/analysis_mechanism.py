"""Failure analysis for the decay reranker (post-hoc, written after the tuning result).

1. How compressed are BM25 scores near the top? (score at rank r / score at rank 1)
2. How large is the decay penalty between a mid-window and a newest paper?
3. Corpus growth by year.
4. Qualitative example: top-10 for q01 under BM25 vs BM25+Decay(h=12) (test query).
"""
import json
import numpy as np, pandas as pd

rk = pd.read_csv("results/rankings.csv.gz")
qm = pd.read_csv("data/query_meta.csv")
docs = pd.read_csv("data/documents.csv", usecols=["paper_id", "title", "publication_date", "year"])
rel = pd.read_csv("data/relevance.csv")
out = {}
b = rk[rk.method == "BM25"].pivot(index="query_id", columns="rank", values="score")
for r in (20, 100, 1000):
    out[f"median_score_ratio_rank{r}_to_rank1"] = float((b[r] / b[1]).median())
for h in (12, 96):
    out[f"decay_factor_29months_h{h}"] = 2 ** (-29 / h)
yc = docs.year.value_counts().sort_index()
out["papers_per_year"] = {int(k): int(v) for k, v in yc.items()}
out["growth_2025_over_2018"] = float(yc[2025] / yc[2018])
out["share_2025_in_corpus"] = float(yc[2025] / yc.sum())
x = rk[(rk.method == "BM25+Decay(h=12)") & (rk["rank"] <= 20)].merge(docs, on="paper_id")
out["share_2025_in_decay12_top20"] = float((x.year == 2025).mean())
x = rk[(rk.method == "BM25") & (rk["rank"] <= 20)].merge(docs, on="paper_id")
out["share_2025_in_bm25_top20"] = float((x.year == 2025).mean())
r_dates = rel.merge(docs, on="paper_id")
out["share_2025_in_relevant"] = float((r_dates.year == 2025).mean())
json.dump(out, open("results/mechanism.json", "w"), indent=1)
print(json.dumps(out, indent=1))

R = set(rel[rel.query_id == "q01"].paper_id)
for m in ["BM25", "BM25+Decay(h=12)"]:
    t = rk[(rk.method == m) & (rk.query_id == "q01") & (rk["rank"] <= 10)].merge(docs, on="paper_id")
    print(f"\n--- q01 {m}")
    for _, r in t.iterrows():
        print(f"{r['rank']:2d} {r.publication_date} {'REL' if r.paper_id in R else '   '} {r.title[:85]}")
