"""Retrieval methods compared in the study (all share one tokenizer and one corpus).

  BM25         Okapi BM25, Lucene/Anserini idf, k1=0.9, b=0.4 (date-unaware baseline)
  TFIDF        sklearn TF-IDF + cosine similarity (second lexical baseline)
  RecencyOnly  BM25 top-N candidates re-sorted by publication date (newest first)
  DateFilter   BM25 restricted to papers dated >= T ("since T" filter)
  BM25+Decay   BM25 top-N re-scored by score * 2^(-age_months / h)   (the intervention)

Adapted from the AI-generated starter `starter_ai_code/retrieval.py`: same tokenizer and
rankings schema (method,query_id,paper_id,rank,score); rank_bm25 replaced by an explicit
sparse-matrix BM25 because rank_bm25 is not installed in the verified environment
(see results/logs/01_starter_environment_test.log).
"""
import re
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())


def months_between(later, earlier):
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


class Corpus:
    def __init__(self, docs: pd.DataFrame, k1=0.9, b=0.4):
        self.docs = docs.reset_index(drop=True)
        self.ids = self.docs["paper_id"].astype(str).to_numpy()
        self.dates = pd.to_datetime(self.docs["publication_date"])
        text = (self.docs["title"].fillna("") + " " + self.docs["abstract"].fillna("")).tolist()
        self.cv = CountVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
        tf = self.cv.fit_transform(text).tocsc().astype(np.float64)     # docs x terms
        N = tf.shape[0]
        dl = np.asarray(tf.sum(axis=1)).ravel()
        self.avgdl = dl.mean()
        df = np.diff(tf.indptr)                                          # per-term doc freq
        self.idf = np.log(1.0 + (N - df + 0.5) / (df + 0.5))
        self.k1, self.b = k1, b
        # precompute BM25 term weights w(d,t) = idf * tf*(k1+1)/(tf + k1*(1-b+b*dl/avgdl))
        tf = tf.tocoo()
        norm = k1 * (1 - b + b * dl[tf.row] / self.avgdl)
        w = self.idf[tf.col] * tf.data * (k1 + 1) / (tf.data + norm)
        self.W = sparse.csc_matrix((w, (tf.row, tf.col)), shape=tf.shape)
        self.tfidf = TfidfVectorizer(tokenizer=tokenize, lowercase=False, token_pattern=None)
        self.X = self.tfidf.fit_transform(text)                          # l2-normalised rows
        self.vocab = self.cv.vocabulary_

    def bm25_scores(self, query):
        q = np.zeros(self.W.shape[1])
        for t in tokenize(query):                 # repeated query terms count repeatedly
            j = self.vocab.get(t)
            if j is not None:
                q[j] += 1
        return np.asarray(self.W @ q).ravel()

    def tfidf_scores(self, query):
        return np.asarray((self.X @ self.tfidf.transform([query]).T).todense()).ravel()


def top_order(scores, ids, n):
    """Indices of the n best scores; ties broken by paper_id ascending (deterministic)."""
    n = min(n, len(scores))
    cand = np.argpartition(-scores, n - 1)[:n] if n < len(scores) else np.arange(len(scores))
    # widen candidate set to include all ties at the boundary
    thr = scores[cand].min()
    cand = np.where(scores >= thr)[0]
    order = sorted(cand, key=lambda i: (-scores[i], ids[i]))
    return np.array(order[:n])


def run_query(C: Corpus, query, method, N=1000, T=None, t_ref=None, h=None):
    """Return (indices, scores) ranked best-first for one query and method."""
    if method == "TFIDF":
        s = C.tfidf_scores(query)
        idx = top_order(s, C.ids, N)
        return idx, s[idx]
    s = C.bm25_scores(query)
    if method == "BM25":
        idx = top_order(s, C.ids, N)
        return idx, s[idx]
    if method == "DateFilter":
        s2 = np.where(C.dates >= T, s, -np.inf)
        idx = top_order(s2, C.ids, N)
        idx = idx[np.isfinite(s2[idx]) & (s2[idx] > 0)]
        return idx, s2[idx]
    pool = top_order(s, C.ids, N)
    pool = pool[s[pool] > 0]
    if method == "RecencyOnly":
        order = sorted(pool, key=lambda i: (-C.dates[i].value, -s[i], C.ids[i]))
        idx = np.array(order)
        return idx, np.array([C.dates[i].year + C.dates[i].month / 12 for i in idx])
    if method == "BM25+Decay":
        if h is None or h == float("inf"):
            new = s[pool]
        else:
            age = np.array([months_between(t_ref, C.dates[i]) for i in pool], dtype=float)
            new = s[pool] * np.power(2.0, -age / h)
        order = sorted(range(len(pool)), key=lambda j: (-new[j], C.ids[pool[j]]))
        return pool[order], new[order]
    raise ValueError(method)
