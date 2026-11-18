"""Per-query metrics. Unlisted papers are non-relevant (binary judgments).

Adapted from starter_ai_code/evaluate.py: the starter refused to score rankings that
contain unjudged papers (it raised ValueError), which is impossible to satisfy with a
62k-document corpus; here unjudged = non-relevant, and this convention is reported.
"""
import math
import numpy as np
import pandas as pd


def dcg(gains):
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def query_metrics(ranked_ids, rel_all, rel_post, k):
    """ranked_ids: list best-first; rel_all/rel_post: sets of relevant ids."""
    top = list(ranked_ids[:k])
    hits = [1 if p in rel_all else 0 for p in top]
    rel_pre = rel_all - rel_post
    out = {
        "P": sum(hits) / k,
        "R_all": sum(hits) / len(rel_all) if rel_all else float("nan"),
        "R_post": len(rel_post.intersection(top)) / len(rel_post) if rel_post else float("nan"),
        "R_pre": len(rel_pre.intersection(top)) / len(rel_pre) if rel_pre else float("nan"),
    }
    ideal = dcg([1] * min(k, len(rel_all)))
    out["nDCG"] = dcg(hits) / ideal if ideal > 0 else float("nan")
    return out


def evaluate(rankings: pd.DataFrame, relevance: pd.DataFrame, ks=(10, 20, 50, 100)):
    rel_all = relevance.groupby("query_id")["paper_id"].apply(set).to_dict()
    rel_post = (relevance[relevance.essential_post_cutoff == 1]
                .groupby("query_id")["paper_id"].apply(set).to_dict())
    rows = []
    for (method, qid), g in rankings.groupby(["method", "query_id"], sort=False):
        ranked = g.sort_values("rank")["paper_id"].tolist()
        assert g["rank"].is_unique, (method, qid)
        for k in ks:
            m = query_metrics(ranked, rel_all.get(qid, set()), rel_post.get(qid, set()), k)
            rows.append({"method": method, "query_id": qid, "k": k, **m})
    return pd.DataFrame(rows)


def paired_bootstrap(diff, n=10000, seed=2026):
    diff = np.asarray(diff, dtype=float)
    diff = diff[~np.isnan(diff)]
    rng = np.random.default_rng(seed)
    means = rng.choice(diff, size=(n, len(diff)), replace=True).mean(axis=1)
    return diff.mean(), np.percentile(means, 2.5), np.percentile(means, 97.5), len(diff)
