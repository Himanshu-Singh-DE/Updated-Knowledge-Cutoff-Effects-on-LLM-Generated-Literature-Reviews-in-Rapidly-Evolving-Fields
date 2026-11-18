"""Run every method for every query; save top-100 rankings and per-query latency.

Labels are NOT read here: rankings are produced without access to relevance judgments.
Usage: python scripts/run_retrieval.py [--cutoffs 2023-07-01 2022-07-01 2024-07-01]
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from retrieval import Corpus, run_query

ap = argparse.ArgumentParser()
ap.add_argument("--exp", default="configs/experiment.json")
ap.add_argument("--out_dir", default="results")
ap.add_argument("--save_k", type=int, default=100)
a = ap.parse_args()
exp = json.load(open(a.exp))
docs = pd.read_csv("data/documents.csv")
queries = pd.read_csv("data/queries.csv")
C = Corpus(docs, k1=exp["bm25"]["k1"], b=exp["bm25"]["b"])
N, t_ref = exp["candidate_pool_N"], pd.Timestamp(exp["t_ref"])
cutoffs = [exp["nominal_cutoff_T"]] + exp["robustness_cutoffs"]
grid = [float("inf") if h == "inf" else float(h) for h in exp["decay"]["h_grid_months"]]

jobs = [("BM25", {}), ("TFIDF", {}), ("RecencyOnly", {})]
jobs += [("BM25+Decay", {"h": h}) for h in grid]
jobs += [("DateFilter", {"T": pd.Timestamp(T)}) for T in cutoffs]
rows, lat = [], []
for name, kw in jobs:
    label = name
    if "h" in kw:
        label = f"BM25+Decay(h={'inf' if kw['h']==float('inf') else int(kw['h'])})"
    if "T" in kw:
        label = f"DateFilter(T={kw['T'].date()})"
    for qid, q in zip(queries.query_id, queries["query"]):
        t0 = time.perf_counter()
        idx, sc = run_query(C, q, name, N=N, t_ref=t_ref, **kw)
        lat.append({"method": label, "query_id": qid, "ms": 1000 * (time.perf_counter() - t0)})
        for r, (i, s) in enumerate(zip(idx[:a.save_k], sc[:a.save_k]), start=1):
            rows.append({"method": label, "query_id": qid, "paper_id": C.ids[i], "rank": r, "score": float(s)})
    print(f"{label:28s} done")
os.makedirs(a.out_dir, exist_ok=True)
pd.DataFrame(rows).to_csv(f"{a.out_dir}/rankings.csv.gz", index=False)
pd.DataFrame(lat).to_csv(f"{a.out_dir}/latency.csv", index=False)
print("rows", len(rows))
