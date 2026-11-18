"""Match entries of human-curated paper lists (GitHub README files) to ACL Anthology records.

A list entry is matched only when an *exact normalised title* of an Anthology paper
(lower-case, alphanumeric tokens) occurs as a contiguous token span in the README line.
Titles shorter than MIN_TOKENS tokens are never matched (too generic). For each line the
longest matching title wins. Output: one row per (list, section path, paper_id).
"""
import argparse, csv, glob, json, os, re
from collections import defaultdict
import pandas as pd

MIN_TOKENS, MAX_TOKENS = 4, 40


def norm_tokens(s):
    return re.findall(r"[a-z0-9]+", str(s).lower())


def clean_heading(h):
    h = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", h)       # markdown links
    h = re.sub(r"[^\w\s\-:&/,()+.']", " ", h)            # emojis / symbols
    return " ".join(h.split()).strip(" -:")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--documents", default="data/documents.csv")
    ap.add_argument("--lists_config", default="configs/lists.json")
    ap.add_argument("--lists_dir", required=True)
    ap.add_argument("--out", default="data/list_matches.csv")
    a = ap.parse_args()
    docs = pd.read_csv(a.documents, usecols=["paper_id", "title"])
    index = defaultdict(list)
    for pid, t in zip(docs.paper_id, docs.title):
        toks = norm_tokens(t)
        if MIN_TOKENS <= len(toks) <= MAX_TOKENS:
            index[" ".join(toks)].append(pid)
    lengths = sorted({len(k.split()) for k in index}, reverse=True)
    cfg = json.load(open(a.lists_config))
    out, summary = [], []
    for item in cfg["lists"]:
        root = os.path.join(a.lists_dir, item["dir"])
        paths = sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True))
        n_match = 0
        for path, line in ((pth, ln) for pth in paths
                           for ln in open(pth, encoding="utf-8", errors="ignore")):
            if path != getattr(main, "_last", None):
                heads, main._last = [], path
            m = re.match(r"^\s*(#{1,6})\s+(.*)$", line)
            if m:
                level = len(m.group(1))
                heads = [h for h in heads if h[0] < level] + [(level, clean_heading(m.group(2)))]
                continue
            toks = norm_tokens(line)
            hit = None
            for L in lengths:
                if L > len(toks):
                    continue
                for i in range(len(toks) - L + 1):
                    key = " ".join(toks[i:i + L])
                    if key in index:
                        hit = key; break
                if hit:
                    break
            if hit:
                n_match += 1
                for pid in index[hit]:
                    out.append({"list": item["name"], "file": os.path.relpath(path, root), "section": " > ".join(h[1] for h in heads),
                                "paper_id": pid, "matched_title": hit,
                                "n_ids_for_title": len(index[hit])})
        summary.append((item["name"], n_match))
    pd.DataFrame(out).to_csv(a.out, index=False)
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
