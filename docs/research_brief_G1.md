# One-page research brief (Gate G1)

| Field | Content |
|---|---|
| Review topic and key papers | Knowledge cutoff effects on LLM-generated literature reviews. Verified sources: Cheng et al. arXiv 2403.12958 (effective vs reported cutoffs); Chelli et al. JMIR 2024;26:e53164 (reference recall 11.9%/13.7%); Vu et al. arXiv 2310.03214 (FreshQA); Shao et al. NAACL 2024 (STORM); Asai et al. arXiv 2411.14199 (OpenScholar) |
| Research gap | Review G1/D1: temporal coverage (TCR) of generated reviews is unmeasured. S5.1 and S7.4: whether retrieval closes the cutoff gap is untested in isolation |
| Research question | Does recency-aware re-ranking (BM25 + exponential decay) raise post-cutoff recall@20 over BM25 on held-out topics without lowering nDCG@20 by more than 0.02? |
| Study pathway | B, controlled comparison (with a C-style isolated modification: the decay term) |
| Dataset / measurement | ACL Anthology XML 2018–2025 (61,877 papers, pinned commit); labels from 34 curated GitHub reading lists (2,305 exact-title matches); 54 queries; split by list |
| Baseline / comparators | BM25 (k1 = 0.9, b = 0.4), TF-IDF; controls: date filter ≥ T, recency-only |
| Primary metric and control | R_post@20; same corpus, tokenizer, queries, labels and candidate pool for all methods; h chosen on tuning lists only |
| Computing and risks | CPU, < 2 GB RAM, about 1 min end-to-end. Risks: incomplete labels, lexical-only methods, ACL-only corpus |
| First executable milestone | Environment test (failed on rank_bm25, fixed) and validated BM25 baseline (logs/01, logs/03) |
