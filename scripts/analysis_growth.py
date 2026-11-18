"""Post-hoc link to the review's severity model (review Eq. 2-4).

1. Estimate the annual growth rate g of ACL Anthology output, 2018-2025, by OLS on ln(count) ~ year,
   using ALL papers (with or without abstract) and, separately, the papers-with-abstract corpus.
2. Evaluate the review's unseen fraction G(g, Delta) = 1 - exp(-g Delta) (review Eq. 3) at the
   review's 18-month example and at Delta = T -> t_ref (29 months).
3. Report BM25 post-cutoff recall at k = 20 and 100 as an empirical value of the review's rho
   (recall of the retrieval stage on post-cutoff work, review Eq. 4) for this lexical retriever.
Usage: python scripts/analysis_growth.py --xml_dir ../data_raw/acl/data/xml
"""
import argparse, glob, json, math, os
import xml.etree.ElementTree as ET
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--xml_dir", required=True)
a = ap.parse_args()
allc = {y: 0 for y in range(2018, 2026)}
for f in sorted(glob.glob(os.path.join(a.xml_dir, "*.xml"))):
    for vol in ET.parse(f).getroot().findall("volume"):
        try:
            y = int("".join(vol.find("meta").find("year").itertext()).strip())
        except Exception:
            continue
        if y in allc:
            allc[y] += len(vol.findall("paper"))
docs = pd.read_csv("data/documents.csv", usecols=["year"])
absc = docs.year.value_counts().sort_index().to_dict()


def fit(counts):
    ys = np.array(sorted(counts)); c = np.array([counts[y] for y in ys], float)
    g, b = np.polyfit(ys, np.log(c), 1)
    resid = np.log(c) - (g * ys + b)
    r2 = 1 - resid.var() / np.log(c).var()
    return float(g), float(r2)


out = {"counts_all_papers": allc, "counts_with_abstract": {int(k): int(v) for k, v in absc.items()}}
for name, cnt in [("all_papers", allc), ("with_abstract", absc)]:
    g, r2 = fit(cnt)
    out[f"g_{name}"], out[f"r2_{name}"] = g, r2
    out[f"doubling_years_{name}"] = math.log(2) / g
    out[f"G_18months_{name}"] = 1 - math.exp(-g * 1.5)
    out[f"G_29months_{name}"] = 1 - math.exp(-g * 29 / 12)
out["G_18months_review_g0085"] = 1 - math.exp(-0.085 * 1.5)
m = pd.read_csv("results/metrics_by_query.csv")
qm = pd.read_csv("data/query_meta.csv")
ids = qm[(qm.split == "test") & qm.active].query_id
for k in (20, 100):
    out[f"rho_BM25_k{k}"] = float(m[(m.method == "BM25") & (m.k == k) & m.query_id.isin(ids)].R_post.mean())
json.dump(out, open("results/growth.json", "w"), indent=1)
print(json.dumps(out, indent=1))
