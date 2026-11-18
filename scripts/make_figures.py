"""Regenerate every paper figure from the result CSVs (no numbers are typed by hand)."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd

OUT = "paper/figures"
os.makedirs(OUT, exist_ok=True)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "legend.frameon": False, "savefig.bbox": "tight", "savefig.dpi": 300})
num = json.load(open("results/numbers.json"))
mech = json.load(open("results/mechanism.json"))
T = num["T"]
NICE = {"BM25": "BM25", "TFIDF": "TF-IDF", "RecencyOnly": "Recency-only",
        f"DateFilter(T={T})": "Date filter (>= T)", "BM25+Decay(h=12)": "BM25+Decay (h=12)",
        "BM25+Decay(h=inf)": "BM25+Decay (h=inf)", "relevant set": "Curated relevant set",
        "whole corpus": "Whole corpus"}

# Fig: sensitivity over h
s = pd.read_csv("results/table_sensitivity.csv")
labels = [str(h).replace(".0", "") if h != "inf" else "inf" for h in s.h.astype(str)]
x = np.arange(len(s))
fig, ax = plt.subplots(figsize=(2.9, 2.3))
ax.plot(x, s.R_post_active, color=BLUE, lw=2, marker="o", ms=4, label="R_post@20 (active)")
ax.plot(x, s.nDCG_active, color=ORANGE, lw=2, marker="s", ms=4, label="nDCG@20 (active)")
ax.plot(x, s.nDCG_stale, color=AQUA, lw=2, marker="^", ms=4, label="nDCG@20 (stale)")
ax.set_xticks(x, labels)
ax.set_xlabel("decay half-life h (months); inf = plain BM25")
ax.set_ylabel("mean over test queries")
ax.legend(loc="upper left", fontsize=7)
fig.savefig(f"{OUT}/fig_sensitivity.pdf")

# Fig: paired differences vs BM25 (forest plot), test active
t = pd.read_csv("results/table_main_test.csv").set_index("method")
meths = ["TFIDF", "RecencyOnly", f"DateFilter(T={T})", "BM25+Decay(h=12)"]
fig, axes = plt.subplots(1, 2, figsize=(6.8, 1.9), sharey=True)
for ax, c, title in [(axes[0], "R_post", "Δ R_post@20 vs BM25"), (axes[1], "nDCG", "Δ nDCG@20 vs BM25")]:
    for i, m in enumerate(meths):
        mu, lo, hi = t.loc[m, f"d_{c}"], t.loc[m, f"d_{c}_lo"], t.loc[m, f"d_{c}_hi"]
        ax.plot([lo, hi], [i, i], color=BLUE, lw=2)
        ax.plot(mu, i, "o", color=BLUE, ms=5, mec="white", mew=1)
        ax.annotate(f"{mu:+.3f}", (hi, i), xytext=(4, 0), textcoords="offset points", va="center", fontsize=7, color=INK)
    ax.axvline(0, color=MUTED, lw=1)
    if c == "R_post":
        ax.axvline(0.05, color=MUTED, lw=1, ls="--")
        ax.text(0.054, 3.45, "success\nthreshold", fontsize=6, color=MUTED, va="center")
    ax.set_title(title, fontsize=8, color=INK)
    ax.set_xlim(-0.26, 0.12)
axes[0].set_yticks(range(len(meths)), [NICE[m] for m in meths])
axes[0].invert_yaxis()
fig.savefig(f"{OUT}/fig_forest.pdf")

# Fig: temporal profile of top-20
p = pd.read_csv("results/table_temporal_profile.csv")
p = p[p.method != "BM25+Decay(h=inf)"]
fig, ax = plt.subplots(figsize=(2.9, 2.3))
y = np.arange(len(p))
ax.barh(y, p.post_share_top20, color=BLUE, height=0.6)
for i, v in enumerate(p.post_share_top20):
    ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=7, color=INK)
ax.set_yticks(y, [NICE.get(m, m) for m in p.method])
ax.invert_yaxis()
ax.set_xlim(0, 1.12)
ax.set_xlabel(f"share dated >= {T}\n(top-20, active test topics)")
fig.savefig(f"{OUT}/fig_temporal_profile.pdf")

# Fig: velocity proxy vs date-filter gain
q = pd.read_csv("results/per_query_test.csv")
r, pv = num["spearman_postshare_dnDCG_DF"]
fig, ax = plt.subplots(figsize=(3.4, 2.2))
ax.axhline(0, color=MUTED, lw=1)
ax.scatter(q.post_share, q.dnDCG_DF, s=22, color=BLUE, edgecolor="white", linewidth=0.8, zorder=3)
ax.set_xlabel("share of a topic's curated papers dated >= T")
ax.set_ylabel("Δ nDCG@20 (date filter − BM25)")
ax.text(0.02, 0.97, f"Spearman ρ = {r:.2f} (p = {pv:.3f}), n = {len(q)}", transform=ax.transAxes,
        va="top", fontsize=7, color=INK)
fig.savefig(f"{OUT}/fig_velocity.pdf")

# Fig: corpus growth
yc = {int(k): v for k, v in mech["papers_per_year"].items()}
fig, ax = plt.subplots(figsize=(3.4, 1.8))
ys = sorted(yc)
ax.bar(ys, [yc[k] for k in ys], color=BLUE, width=0.7)
ax.set_xticks([int(k) for k in ys], ["'" + str(k)[2:] for k in ys])
ax.set_ylabel("papers with abstracts")
ax.axvline(2023.0, color=MUTED, lw=1, ls="--")
ax.text(2022.9, max(yc.values()) * 0.95, "T = 2023-07", fontsize=6.5, color=MUTED, ha="right")
fig.savefig(f"{OUT}/fig_corpus_growth.pdf")
print("figures written to", OUT)
