"""Step 2 of evaluation (run AFTER select_h.py): held-out test results + deeper analyses.

Outputs (results/):
  metrics_by_query.csv      every method x query x k (main cutoff T)
  table_main_test.csv       RQ1/RQ2: test active queries, k=20, mean and paired diffs vs BM25
  table_stale_test.csv      RQ3: test queries with no post-cutoff relevant papers
  table_sensitivity.csv     post-hoc: every h on test (active and stale)
  table_cutoff_robustness.csv  T in {2022-07, 2023-07, 2024-07}
  table_condensed.csv       post-hoc: evaluation inside each list's coverage window
  table_temporal_profile.csv  share of post-cutoff papers in top-20 vs relevant sets
  per_query_test.csv        per-query deltas used for failure / velocity analysis
  latency_summary.csv
  numbers.json              every number quoted in the paper
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from scipy import stats
from metrics import evaluate, paired_bootstrap

exp = json.load(open("configs/experiment.json"))
T = exp["nominal_cutoff_T"]
h_star = json.load(open("results/selected_h.json"))["h_star_months"]
h_lab = "inf" if h_star == float("inf") else str(int(h_star))
DEC = f"BM25+Decay(h={h_lab})"
DF = f"DateFilter(T={T})"
docs = pd.read_csv("data/documents.csv", usecols=["paper_id", "publication_date"])
date = dict(zip(docs.paper_id, docs.publication_date))
rk = pd.read_csv("results/rankings.csv.gz")
rel = pd.read_csv("data/relevance.csv")
qm = pd.read_csv("data/query_meta.csv")
num = {"T": T, "h_star": h_lab, "n_docs": len(docs)}

M = evaluate(rk, rel)
M.to_csv("results/metrics_by_query.csv", index=False)
test_act = qm[(qm.split == "test") & qm.active].query_id.tolist()
test_stale = qm[(qm.split == "test") & ~qm.active].query_id.tolist()
num.update(n_queries=len(qm), n_test_active=len(test_act), n_test_stale=len(test_stale),
           n_tune=int((qm.split == "tuning").sum()), n_tune_active=int(((qm.split == "tuning") & qm.active).sum()),
           n_judgments=len(rel), n_post_judgments=int(rel.essential_post_cutoff.sum()),
           n_lists=qm.group.str.split("+").explode().nunique())


def compare(Mk, qids, methods, base="BM25", cols=("R_post", "nDCG", "R_pre", "P", "R_all"), tag=""):
    out = []
    b = Mk[(Mk.method == base) & Mk.query_id.isin(qids)].set_index("query_id")
    for m in methods:
        x = Mk[(Mk.method == m) & Mk.query_id.isin(qids)].set_index("query_id")
        row = {"method": m, "n": len(x)}
        for c in cols:
            row[c] = x[c].mean()
            if m != base:
                d = (x[c] - b.loc[x.index, c]).values
                mu, lo, hi, n = paired_bootstrap(d, exp["uncertainty"]["bootstrap_resamples"],
                                                 exp["uncertainty"]["bootstrap_seed"])
                dd = d[~np.isnan(d)]
                p = stats.wilcoxon(dd).pvalue if np.any(dd != 0) else 1.0
                row.update({f"d_{c}": mu, f"d_{c}_lo": lo, f"d_{c}_hi": hi, f"p_{c}": p, f"n_{c}": n})
        out.append(row)
    return pd.DataFrame(out)


M20 = M[M.k == 20]
main_methods = ["BM25", "TFIDF", "RecencyOnly", DF, DEC, "BM25+Decay(h=12)"]
main_methods = list(dict.fromkeys(main_methods))
tab = compare(M20, test_act, main_methods)
tab.to_csv("results/table_main_test.csv", index=False)
stale = compare(M20, test_stale, main_methods, cols=("nDCG", "P", "R_all"))
stale.to_csv("results/table_stale_test.csv", index=False)

# R_post at several k (test active)
rk_k = M[M.query_id.isin(test_act) & M.method.isin(main_methods)].groupby(["method", "k"])[["R_post", "nDCG"]].mean().reset_index()
rk_k.to_csv("results/table_by_k.csv", index=False)

# sensitivity over h (post-hoc on test)
hs = [m for m in M.method.unique() if m.startswith("BM25+Decay")]
sens = []
for m in hs:
    h = m.split("=")[1].rstrip(")")
    a = M20[(M20.method == m) & M20.query_id.isin(test_act)]
    s = M20[(M20.method == m) & M20.query_id.isin(test_stale)]
    sens.append({"h": h, "R_post_active": a.R_post.mean(), "nDCG_active": a.nDCG.mean(),
                 "R_pre_active": a.R_pre.mean(), "nDCG_stale": s.nDCG.mean()})
sens = pd.DataFrame(sens)
sens["h_num"] = sens.h.replace("inf", "1e9").astype(float)
sens.sort_values("h_num").drop(columns="h_num").to_csv("results/table_sensitivity.csv", index=False)

# temporal profile of top-20
prof = []
for m in main_methods:
    x = rk[(rk.method == m) & (rk["rank"] <= 20) & rk.query_id.isin(test_act)]
    prof.append({"method": m, "post_share_top20": np.mean([date[p] >= T for p in x.paper_id]),
                 "median_year_top20": float(np.median([int(date[p][:4]) for p in x.paper_id]))})
r_act = rel[rel.query_id.isin(test_act)]
prof.append({"method": "relevant set", "post_share_top20": r_act.essential_post_cutoff.mean(),
             "median_year_top20": float(np.median([int(date[p][:4]) for p in r_act.paper_id]))})
prof.append({"method": "whole corpus", "post_share_top20": float((docs.publication_date >= T).mean()),
             "median_year_top20": float(docs.publication_date.str[:4].astype(int).median())})
pd.DataFrame(prof).to_csv("results/table_temporal_profile.csv", index=False)

# cutoff robustness
rob = []
for TT in [T] + exp["robustness_cutoffs"]:
    sfx = "" if TT == T else "_T" + TT
    relT, qmT = pd.read_csv(f"data/relevance{sfx}.csv"), pd.read_csv(f"data/query_meta{sfx}.csv")
    ids = qmT[(qmT.split == "test") & qmT.active].query_id.tolist()
    meths = ["BM25", "RecencyOnly", f"DateFilter(T={TT})", "BM25+Decay(h=12)"]
    MT = evaluate(rk[rk.method.isin(meths) & rk.query_id.isin(ids)], relT, ks=(20,))
    t = compare(MT, ids, meths, cols=("R_post", "nDCG", "R_pre"))
    t.insert(0, "T", TT)
    rob.append(t)
pd.concat(rob).to_csv("results/table_cutoff_robustness.csv", index=False)

# condensed evaluation inside each list's coverage window (post-hoc)
grp = dict(zip(qm.query_id, qm.group))
win = {}
for g in qm.group.unique():
    ids = qm[qm.group == g].query_id
    win[g] = rel[rel.query_id.isin(ids)].paper_id.map(date).max()
rkc = rk.copy()
rkc["end"] = rkc.query_id.map(grp).map(win)
rkc = rkc[rkc.paper_id.map(date) <= rkc.end].copy()
rkc["rank"] = rkc.groupby(["method", "query_id"])["rank"].rank(method="first").astype(int)
MC = evaluate(rkc[rkc.method.isin(main_methods)], rel, ks=(20,))
cond = compare(MC, test_act, main_methods)
cond.to_csv("results/table_condensed.csv", index=False)
num["window_ends"] = {g: w for g, w in sorted(win.items())}
num["n_lists_window_before_2025_06"] = int(sum(w < "2025-06-01" for w in win.values()))

# per-query deltas (test active) + velocity correlation
b = M20[M20.method == "BM25"].set_index("query_id")
pq = qm[qm.query_id.isin(test_act)].set_index("query_id")[["query", "group", "n_relevant", "n_post"]].copy()
pq["post_share"] = pq.n_post / pq.n_relevant
for m, tagm in [(DF, "DF"), ("BM25+Decay(h=12)", "Dec12"), ("RecencyOnly", "Rec")]:
    x = M20[M20.method == m].set_index("query_id")
    pq[f"dnDCG_{tagm}"] = x.loc[pq.index, "nDCG"] - b.loc[pq.index, "nDCG"]
    pq[f"dRpost_{tagm}"] = x.loc[pq.index, "R_post"] - b.loc[pq.index, "R_post"]
pq["BM25_nDCG"] = b.loc[pq.index, "nDCG"]
pq["BM25_Rpost"] = b.loc[pq.index, "R_post"]
pq.to_csv("results/per_query_test.csv")
for tagm in ["DF", "Dec12"]:
    r, p = stats.spearmanr(pq.post_share, pq[f"dnDCG_{tagm}"])
    num[f"spearman_postshare_dnDCG_{tagm}"] = [r, p]
num["n_queries_DF_helps_nDCG"] = int((pq.dnDCG_DF > 0).sum())
num["n_queries_DF_hurts_nDCG"] = int((pq.dnDCG_DF < 0).sum())
num["n_queries_Dec12_hurts_nDCG"] = int((pq.dnDCG_Dec12 < 0).sum())
num["n_queries_Dec12_helps_nDCG"] = int((pq.dnDCG_Dec12 > 0).sum())

lat = pd.read_csv("results/latency.csv")
ls = lat.groupby("method").ms.agg(["mean", "median", lambda s: s.quantile(.95)]).rename(columns={"<lambda_0>": "p95"})
ls.to_csv("results/latency_summary.csv")
json.dump(num, open("results/numbers.json", "w"), indent=1, default=float)
pd.set_option("display.width", 250)
for f in ["table_main_test", "table_stale_test", "table_sensitivity", "table_temporal_profile",
          "table_cutoff_robustness", "table_condensed", "table_by_k", "latency_summary"]:
    print(f"\n=== {f}\n", pd.read_csv(f"results/{f}.csv").round(4).to_string())
print(json.dumps({k: v for k, v in num.items() if k != "window_ends"}, indent=1, default=float))
print(pq.sort_values("dnDCG_DF").round(3)[["query", "post_share", "BM25_nDCG", "dnDCG_DF", "dnDCG_Dec12", "dRpost_DF"]].to_string())
