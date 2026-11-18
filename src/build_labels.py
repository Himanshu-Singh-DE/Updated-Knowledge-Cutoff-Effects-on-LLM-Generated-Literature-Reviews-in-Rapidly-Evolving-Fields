"""Turn list matches + frozen query spec into queries.csv / relevance.csv / query_meta.csv.

relevance.csv keeps the starter-code schema:
    query_id,paper_id,relevance_grade,essential_post_cutoff
relevance_grade is 1 for every curated paper (binary judgments); essential_post_cutoff
is 1 when publication_date >= T. Splits are assigned per source list with a fixed seed.
"""
import argparse, json, re
import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--documents", default="data/documents.csv")
    ap.add_argument("--matches", default="data/list_matches.csv")
    ap.add_argument("--spec", default="configs/queries_spec.json")
    ap.add_argument("--exp", default="configs/experiment.json")
    ap.add_argument("--cutoff", default=None, help="override T (robustness runs)")
    ap.add_argument("--out_dir", default="data")
    a = ap.parse_args()
    exp = json.load(open(a.exp))
    T = a.cutoff or exp["nominal_cutoff_T"]
    docs = pd.read_csv(a.documents, usecols=["paper_id", "publication_date"])
    m = pd.read_csv(a.matches).merge(docs, on="paper_id")
    m["section"] = m["section"].fillna("")
    q_rows, r_rows = [], []
    for q in json.load(open(a.spec))["queries"]:
        x = m[m["list"].isin(q["lists"])]
        if q["file_contains"]:
            x = x[x["file"].str.contains(q["file_contains"], regex=False)]
        if q["section_regex"]:
            x = x[x["section"].str.contains(q["section_regex"], flags=re.I, regex=True)]
        x = x.drop_duplicates("paper_id")
        n_post = int((x.publication_date >= T).sum())
        q_rows.append({"query_id": q["query_id"], "query": q["query"], "group": "+".join(q["lists"]),
                       "n_relevant": len(x), "n_post": n_post, "n_pre": len(x) - n_post})
        for pid, d in zip(x.paper_id, x.publication_date):
            r_rows.append({"query_id": q["query_id"], "paper_id": pid, "relevance_grade": 1,
                           "essential_post_cutoff": int(d >= T)})
    qm = pd.DataFrame(q_rows)
    qm = qm[qm.n_relevant >= exp["query_inclusion"]["min_relevant"]].copy()
    qm["active"] = qm.n_post >= 3
    # split by source list (group), fixed seed, independent of results
    groups = sorted(qm.group.unique())
    rng = np.random.default_rng(exp["split"]["seed"])
    perm = rng.permutation(groups)
    n_tune = int(round(exp["split"]["tuning_fraction_of_lists"] * len(groups)))
    tune = set(perm[:n_tune])
    qm["split"] = np.where(qm.group.isin(tune), "tuning", "test")
    rel = pd.DataFrame(r_rows)
    rel = rel[rel.query_id.isin(qm.query_id)]
    sfx = "" if a.cutoff is None else "_T" + T
    qm[["query_id", "query"]].to_csv(f"{a.out_dir}/queries.csv", index=False)
    rel.to_csv(f"{a.out_dir}/relevance{sfx}.csv", index=False)
    qm.to_csv(f"{a.out_dir}/query_meta{sfx}.csv", index=False)
    print(f"T={T} queries={len(qm)} active={int(qm.active.sum())} "
          f"tuning={int((qm.split=='tuning').sum())} (active {int((qm.active&(qm.split=='tuning')).sum())}) "
          f"test={int((qm.split=='test').sum())} (active {int((qm.active&(qm.split=='test')).sum())}) "
          f"judgments={len(rel)} post={int(rel.essential_post_cutoff.sum())}")


if __name__ == "__main__":
    main()
