"""Step 1 of evaluation: choose the decay half-life h using TUNING queries only.
Test-query metrics are not computed or printed by this script.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas as pd
from metrics import evaluate

exp = json.load(open("configs/experiment.json"))
qm = pd.read_csv("data/query_meta.csv")
tune = qm[(qm.split == "tuning") & qm.active].query_id
rk = pd.read_csv("results/rankings.csv.gz")
rk = rk[rk.query_id.isin(tune) & (rk.method.str.startswith("BM25"))]
rel = pd.read_csv("data/relevance.csv")
m = evaluate(rk, rel, ks=(20,))
g = m.groupby("method")[["R_post", "nDCG"]].mean()
base = g.loc["BM25", "nDCG"]
g["h"] = [float("inf") if "inf" in i else (float(i.split("=")[1].rstrip(")")) if "h=" in i else None) for i in g.index]
grid = g.dropna(subset=["h"]).copy()
grid["guardrail_ok"] = grid.nDCG >= base - 0.02
ok = grid[grid.guardrail_ok].sort_values(["R_post", "h"], ascending=[False, False])
h_star = ok.iloc[0]["h"]
print(f"tuning active queries: {list(tune)}")
print(g.round(4).to_string())
print(f"BM25 tuning nDCG@20 = {base:.4f}; guardrail >= {base-0.02:.4f}")
print(f"SELECTED h* = {h_star}")
grid.to_csv("results/tuning_grid.csv")
json.dump({"h_star_months": h_star, "selected_on": list(tune),
           "rule": exp["selection_rule"]}, open("results/selected_h.json", "w"), indent=1)
