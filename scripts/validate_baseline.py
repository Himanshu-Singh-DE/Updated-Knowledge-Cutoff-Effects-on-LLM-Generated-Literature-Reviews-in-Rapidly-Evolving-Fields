"""Gate G2: check the BM25 baseline and the metrics before any comparison is run.

1. Toy corpus: sparse BM25 vs an independent pure-Python loop and a hand-computed value.
2. Real corpus: sparse BM25 vs the pure-Python loop on 3 queries over all documents.
3. Known-item test: a paper's exact title used as the query should return it at rank 1.
4. Metric toy case with hand-computed P, recall, nDCG.
5. Label spot-check: random sample of list matches printed for manual inspection.
Writes results/logs/03_baseline_validation.log (stdout).
"""
import math, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
from retrieval import Corpus, tokenize, run_query
from metrics import query_metrics


def loop_bm25(doc_tokens, query, k1=0.9, b=0.4):
    N = len(doc_tokens); avgdl = sum(map(len, doc_tokens)) / N
    df = {}
    for d in doc_tokens:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    out = []
    for d in doc_tokens:
        s = 0.0
        for t in tokenize(query):
            if t not in df:
                continue
            tf = d.count(t)
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avgdl))
        out.append(s)
    return np.array(out)


print("== 1. toy corpus")
toy = pd.DataFrame({"paper_id": ["d1", "d2", "d3"],
                    "title": ["knowledge cutoff", "retrieval augmented generation", "knowledge editing knowledge"],
                    "abstract": ["", "", ""], "publication_date": ["2020-01-01", "2023-01-01", "2025-01-01"]})
C = Corpus(toy)
s_sparse = C.bm25_scores("knowledge")
s_loop = loop_bm25([tokenize(t) for t in toy.title], "knowledge")
# hand computation: N=3, df(knowledge)=2, idf=ln(1+(3-2+0.5)/(2+0.5))=ln(1.6)=0.470004
# avgdl=(2+3+3)/3=2.6667. d1: tf=1, dl=2 -> 0.470004*1*1.9/(1+0.9*(0.6+0.4*2/2.6667)) = 0.470004*1.9/1.81
hand_d1 = math.log(1.6) * 1.9 / (1 + 0.9 * (0.6 + 0.4 * 2 / (8 / 3)))
print("sparse", np.round(s_sparse, 6), "loop", np.round(s_loop, 6), "hand d1", round(hand_d1, 6))
assert np.allclose(s_sparse, s_loop) and abs(s_sparse[0] - hand_d1) < 1e-9
print("decay check: d3 (2025) vs d1 (2020) with h=12, t_ref=2025-12-01")
idx, sc = run_query(C, "knowledge", "BM25+Decay", N=10, t_ref=pd.Timestamp("2025-12-01"), h=12)
print([C.ids[i] for i in idx], np.round(sc, 6))
idx, sc = run_query(C, "knowledge", "DateFilter", N=10, T=pd.Timestamp("2023-07-01"))
print("DateFilter T=2023-07-01 ->", [C.ids[i] for i in idx])

print("\n== 2. real corpus: sparse vs loop")
docs = pd.read_csv("data/documents.csv")
t0 = time.time(); C = Corpus(docs); print(f"index built in {time.time()-t0:.1f}s; docs={len(docs)} vocab={len(C.vocab)} avgdl={C.avgdl:.2f}")
toks = [tokenize(a + " " + b) for a, b in zip(docs.title.fillna(""), docs.abstract.fillna(""))]
for q in ["knowledge editing for large language models", "neural machine translation", "event extraction"]:
    a, b = C.bm25_scores(q), loop_bm25(toks, q)
    print(f"{q!r}: max|diff|={np.abs(a-b).max():.2e}  top1 sparse={C.ids[a.argmax()]} loop={C.ids[b.argmax()]}")
    assert np.allclose(a, b, atol=1e-9)

print("\n== 3. known-item test (exact title as query), 200 random papers, seed 2026")
rng = np.random.default_rng(2026)
sample = rng.choice(len(docs), 200, replace=False)
r1 = r10 = 0
for i in sample:
    idx, _ = run_query(C, docs.title[i], "BM25", N=10)
    ids = [C.ids[j] for j in idx]
    r1 += ids[0] == C.ids[i]; r10 += C.ids[i] in ids
print(f"rank-1: {r1}/200  in top-10: {r10}/200")
idx, _ = run_query(C, docs.title[sample[0]], "TFIDF", N=10)
print("TFIDF known-item sample:", C.ids[sample[0]], "->", C.ids[idx[0]])

print("\n== 4. metric toy case")
m = query_metrics(["a", "x", "b", "y"], {"a", "b", "c"}, {"b", "c"}, k=4)
# hits=[1,0,1,0]; P=2/4; R_all=2/3; R_post=1/2 (b); R_pre=1/1 (a)
# DCG=1/log2(2)+1/log2(4)=1.5; IDCG(3 rel)=1+1/log2(3)+1/log2(4)=2.130930; nDCG=0.703918
print({k: round(v, 6) for k, v in m.items()})
assert abs(m["P"] - 0.5) < 1e-12 and abs(m["R_all"] - 2/3) < 1e-12 and m["R_post"] == 0.5 and m["R_pre"] == 1.0
assert abs(m["nDCG"] - 1.5 / (1 + 1/math.log2(3) + 0.5)) < 1e-12

print("\n== 5. label spot-check (20 random matches)")
lm = pd.read_csv("data/list_matches.csv").merge(docs[["paper_id", "title", "publication_date"]], on="paper_id")
print("matched lines:", len(lm), " titles mapping to >1 Anthology id:", int((lm.n_ids_for_title > 1).sum()))
for _, r in lm.sample(20, random_state=2026).iterrows():
    print(f"[{r['list'][:28]}] {r.paper_id} {r.publication_date} | {r.title[:80]}")
print("\nALL BASELINE CHECKS PASSED")
