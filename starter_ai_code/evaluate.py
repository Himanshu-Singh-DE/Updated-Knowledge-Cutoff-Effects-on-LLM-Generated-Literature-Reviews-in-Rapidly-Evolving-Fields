import argparse
import os
import math
import pandas as pd

def dcg(relevances):
    return sum((2 ** int(rel) - 1) / math.log2(i + 2) for i, rel in enumerate(relevances))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rankings", required=True, help="CSV with method,query_id,paper_id,rank")
    p.add_argument("--relevance", required=True, help="CSV with query_id,paper_id,relevance_grade,essential_post_cutoff")
    p.add_argument("--out", default="results/metrics_by_query.csv")
    p.add_argument("--k", type=int, default=10)
    a = p.parse_args()
    ranks = pd.read_csv(a.rankings)
    rel = pd.read_csv(a.relevance)

    if not {"method","query_id","paper_id","rank"}.issubset(ranks.columns):
        raise ValueError("rankings CSV missing required columns")
    required_rel = {"query_id","paper_id","relevance_grade","essential_post_cutoff"}
    if not required_rel.issubset(rel.columns):
        raise ValueError(f"relevance CSV must contain {sorted(required_rel)}")
    if ranks.duplicated(["method","query_id","paper_id"]).any():
        raise ValueError("Duplicate method/query_id/paper_id rows in rankings")
    if rel.duplicated(["query_id","paper_id"]).any():
        raise ValueError("Duplicate query_id/paper_id rows in relevance labels")
    if ranks[["query_id","paper_id","rank"]].isna().any().any():
        raise ValueError("Missing query, paper or rank in rankings")
    known = set(zip(rel["query_id"], rel["paper_id"]))
    unknown = [(q,p) for q,p in zip(ranks["query_id"], ranks["paper_id"]) if (q,p) not in known]
    if unknown:
        raise ValueError(f"{len(unknown)} ranked query-paper pairs lack relevance labels; resolve before scoring")

    merged = ranks.merge(rel, on=["query_id","paper_id"], how="left", validate="one_to_one")
    rows = []
    for (method, qid), group in merged.groupby(["method","query_id"], sort=False):
        top = group.sort_values("rank").head(a.k)
        all_relevant = rel[(rel["query_id"] == qid) & (rel["relevance_grade"] > 0)]
        essential = rel[(rel["query_id"] == qid) & (rel["essential_post_cutoff"].astype(str).str.lower().isin(["1","true","yes"]))]
        found_rel = int((top["relevance_grade"] > 0).sum())
        found_essential = int(top["essential_post_cutoff"].astype(str).str.lower().isin(["1","true","yes"]).sum())
        precision = found_rel / a.k
        recall = found_rel / len(all_relevant) if len(all_relevant) else float("nan")
        essential_recall = found_essential / len(essential) if len(essential) else float("nan")
        actual = top["relevance_grade"].astype(int).tolist()
        ideal = sorted(rel[rel["query_id"] == qid]["relevance_grade"].astype(int).tolist(), reverse=True)[:a.k]
        idcg = dcg(ideal)
        ndcg = dcg(actual) / idcg if idcg > 0 else float("nan")
        rows.append({"method":method,"query_id":qid,"k":a.k,"precision_at_k":precision,
                     "recall_at_k":recall,"essential_post_cutoff_recall_at_k":essential_recall,"ndcg_at_k":ndcg})
    result = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    result.to_csv(a.out, index=False)
    print(f"Wrote per-query metrics to {a.out}")
    print("These are computed only from supplied labels; audit label completeness before interpreting.")
if __name__ == "__main__":
    main()
