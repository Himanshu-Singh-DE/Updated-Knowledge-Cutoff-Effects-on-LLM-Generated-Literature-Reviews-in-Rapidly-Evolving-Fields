import argparse
import os
import re
import pandas as pd
from rank_bm25 import BM25Okapi

def tokenize(text):
    return re.findall(r"[a-z0-9]+", str(text).lower())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data")
    parser.add_argument("--out", default="results/bm25_rankings.csv")
    parser.add_argument("--top_k", type=int, default=20)
    args = parser.parse_args()

    docs_path = os.path.join(args.data_dir, "documents.csv")
    queries_path = os.path.join(args.data_dir, "queries.csv")
    docs = pd.read_csv(docs_path)
    queries = pd.read_csv(queries_path)

    required_docs = {"paper_id", "title", "abstract", "publication_date"}
    required_queries = {"query_id", "query"}
    if not required_docs.issubset(docs.columns):
        raise ValueError(f"documents.csv must contain columns: {sorted(required_docs)}")
    if not required_queries.issubset(queries.columns):
        raise ValueError(f"queries.csv must contain columns: {sorted(required_queries)}")
    if docs["paper_id"].isna().any() or docs["paper_id"].duplicated().any():
        raise ValueError("paper_id values must be nonmissing and unique")
    if queries["query_id"].isna().any() or queries["query_id"].duplicated().any():
        raise ValueError("query_id values must be nonmissing and unique")

    text = (docs["title"].fillna("") + " " + docs["abstract"].fillna("")).tolist()
    tokenized_docs = [tokenize(x) for x in text]
    if not tokenized_docs or not any(tokenized_docs):
        raise ValueError("No searchable document tokens found")
    bm25 = BM25Okapi(tokenized_docs)

    rows = []
    for _, q in queries.iterrows():
        tokens = tokenize(q["query"])
        scores = bm25.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: (-scores[i], str(docs.iloc[i]["paper_id"])))
        for rank, idx in enumerate(ranked_indices[:args.top_k], start=1):
            rows.append({
                "method": "BM25",
                "query_id": q["query_id"],
                "paper_id": docs.iloc[idx]["paper_id"],
                "rank": rank,
                "score": float(scores[idx])
            })
    result = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    result.to_csv(args.out, index=False)
    print(f"Wrote {len(result)} ranked rows to {args.out}")
    print("Reminder: inspect sample rankings and verify the corpus before interpreting metrics.")

if __name__ == "__main__":
    main()
