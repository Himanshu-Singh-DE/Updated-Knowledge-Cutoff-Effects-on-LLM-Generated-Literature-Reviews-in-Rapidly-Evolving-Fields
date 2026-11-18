"""Write LaTeX tables and number macros from result files (paper/generated/*.tex).
Every number in the paper's results comes from these generated files."""
import json, os, re
import pandas as pd

OUT = "paper/generated"
os.makedirs(OUT, exist_ok=True)
num = json.load(open("results/numbers.json"))
mech = json.load(open("results/mechanism.json"))
T = num["T"]
NICE = {"BM25": "BM25", "TFIDF": "TF-IDF", "RecencyOnly": "Recency-only",
        f"DateFilter(T={T})": "Date filter $\\geq T$", "BM25+Decay(h=inf)": "Decay $h^{*}{=}\\infty$",
        "BM25+Decay(h=12)": "Decay $h{=}12$ (post hoc)"}


def f3(x):
    return f"{x:.3f}"


def ci(r, c):
    return f"{r[f'd_{c}']:+.3f} [{r[f'd_{c}_lo']:+.3f}, {r[f'd_{c}_hi']:+.3f}]"


def tex_signs(s):
    s = re.sub(r"(?<![\d\-])-(\d)", r"$-$\1", str(s))
    return re.sub(r"(?<![\d])\+(\d)", r"$+$\1", s)


macros = {}
def mac(name, val):
    macros[name] = val

# dataset
qm = pd.read_csv("data/query_meta.csv")
mac("NDocs", f"{num['n_docs']:,}"); mac("NQueries", num["n_queries"]); mac("NLists", num["n_lists"])
mac("NJudg", f"{num['n_judgments']:,}"); mac("NPostJudg", num["n_post_judgments"])
mac("NTestAct", num["n_test_active"]); mac("NTestStale", num["n_test_stale"])
mac("NTune", num["n_tune"]); mac("NTuneAct", num["n_tune_active"])
mac("NActive", int(qm.active.sum())); mac("NStale", int((~qm.active).sum()))
mac("MedRel", int(qm.n_relevant.median()))

# tuning grid
g = pd.read_csv("results/tuning_grid.csv").set_index("method")
rows = []
for h in ["3", "6", "12", "24", "48", "96", "inf"]:
    r = g.loc[f"BM25+Decay(h={h})"]
    hh = "$\\infty$ (= BM25)" if h == "inf" else h
    rows.append(f"{hh} & {f3(r.R_post)} & {f3(r.nDCG)} & {'yes' if r.guardrail_ok else 'no'} \\\\")
open(f"{OUT}/tab_tuning.tex", "w").write(tex_signs("\n".join(rows)))
mac("TuneBMRpost", f3(g.loc["BM25+Decay(h=inf)", "R_post"])); mac("TuneBMnDCG", f3(g.loc["BM25+Decay(h=inf)", "nDCG"]))
mac("TuneGuard", f3(g.loc["BM25+Decay(h=inf)", "nDCG"] - 0.02))
fin = g[g.h != float("inf")].dropna(subset=["h"])
mac("TuneBestFiniteRpost", f3(fin.R_post.max())); mac("TuneBestFiniteH", int(fin.R_post.idxmax().split("=")[1].rstrip(")")))

# main test table
t = pd.read_csv("results/table_main_test.csv").set_index("method")
order = ["BM25", "TFIDF", "RecencyOnly", f"DateFilter(T={T})", "BM25+Decay(h=inf)", "BM25+Decay(h=12)"]
rows = []
for m in order:
    r = t.loc[m]
    if m == "BM25":
        rows.append(f"{NICE[m]} & {f3(r.R_post)} & -- & {f3(r.nDCG)} & -- & {f3(r.R_pre)} \\\\")
    else:
        rows.append(f"{NICE[m]} & {f3(r.R_post)} & {ci(r, 'R_post')} & {f3(r.nDCG)} & {ci(r, 'nDCG')} & {f3(r.R_pre)} \\\\")
open(f"{OUT}/tab_main.tex", "w").write(tex_signs("\n".join(rows)))
DF, DEC = t.loc[f"DateFilter(T={T})"], t.loc["BM25+Decay(h=12)"]
mac("BMRpost", f3(t.loc["BM25", "R_post"])); mac("BMnDCG", f3(t.loc["BM25", "nDCG"])); mac("BMRpre", f3(t.loc["BM25", "R_pre"]))
mac("DFRpost", f3(DF.R_post)); mac("DFdRpost", f"{DF.d_R_post:+.3f}"); mac("DFdRpostCI", f"[{DF.d_R_post_lo:+.3f}, {DF.d_R_post_hi:+.3f}]")
mac("DFdnDCG", f"{DF.d_nDCG:+.3f}"); mac("DFdnDCGCI", f"[{DF.d_nDCG_lo:+.3f}, {DF.d_nDCG_hi:+.3f}]"); mac("DFpRpost", f"{DF.p_R_post:.3f}")
mac("DecdRpost", f"{DEC.d_R_post:+.3f}"); mac("DecdRpostCI", f"[{DEC.d_R_post_lo:+.3f}, {DEC.d_R_post_hi:+.3f}]")
mac("DecdnDCG", f"{DEC.d_nDCG:+.3f}"); mac("DecdnDCGCI", f"[{DEC.d_nDCG_lo:+.3f}, {DEC.d_nDCG_hi:+.3f}]")
mac("TFdRpost", f"{t.loc['TFIDF','d_R_post']:+.3f}"); mac("TFdnDCG", f"{t.loc['TFIDF','d_nDCG']:+.3f}")
mac("RecdRpost", f"{t.loc['RecencyOnly','d_R_post']:+.3f}"); mac("RecdnDCG", f"{t.loc['RecencyOnly','d_nDCG']:+.3f}")

# stale
s = pd.read_csv("results/table_stale_test.csv").set_index("method")
rows = []
for m in order:
    r = s.loc[m]
    d = "--" if m == "BM25" else ci(r, "nDCG")
    rows.append(f"{NICE[m]} & {f3(r.nDCG)} & {d} & {f3(r.P)} \\\\")
open(f"{OUT}/tab_stale.tex", "w").write(tex_signs("\n".join(rows)))
mac("StaleBMnDCG", f3(s.loc["BM25", "nDCG"]))

# cutoff robustness
rb = pd.read_csv("results/table_cutoff_robustness.csv")
rows = []
for TT, x in rb.groupby("T", sort=False):
    x = x.set_index("method")
    b = x.loc["BM25"]
    d, dc = x.loc[f"DateFilter(T={TT})"], x.loc["BM25+Decay(h=12)"]
    rows.append(f"{TT} & {int(b.n)} & BM25 (absolute) & {f3(b.R_post)} & {f3(b.nDCG)} \\\\")
    rows.append(f" & & Date filter $\\Delta$ & {ci(d,'R_post')} & {ci(d,'nDCG')} \\\\")
    rows.append(f" & & Decay $h{{=}}12$ $\\Delta$ & {ci(dc,'R_post')} & {ci(dc,'nDCG')} \\\\\\addlinespace")
open(f"{OUT}/tab_cutoff.tex", "w").write(tex_signs("\n".join(rows)))

# coverage-window evaluation
c = pd.read_csv("results/table_condensed.csv").set_index("method")
mac("CondDFdRpost", ci(c.loc[f"DateFilter(T={T})"], "R_post")); mac("CondDFdnDCG", ci(c.loc[f"DateFilter(T={T})"], "nDCG"))
mac("CondDecdRpost", ci(c.loc["BM25+Decay(h=12)"], "R_post")); mac("CondDecdnDCG", ci(c.loc["BM25+Decay(h=12)"], "nDCG"))
mac("CondBMRpost", f3(c.loc["BM25", "R_post"])); mac("NListsWindowEarly", num["n_lists_window_before_2025_06"])

# temporal profile & mechanism
p = pd.read_csv("results/table_temporal_profile.csv").set_index("method")
mac("BMPostShare", f"{p.loc['BM25','post_share_top20']:.2f}"); mac("RelPostShare", f"{p.loc['relevant set','post_share_top20']:.2f}")
mac("CorpusPostShare", f"{p.loc['whole corpus','post_share_top20']:.2f}"); mac("TFPostShare", f"{p.loc['TFIDF','post_share_top20']:.2f}")
mac("RatioTwenty", f"{mech['median_score_ratio_rank20_to_rank1']:.2f}"); mac("RatioHundred", f"{mech['median_score_ratio_rank100_to_rank1']:.2f}")
mac("DecayFacTwelve", f"{mech['decay_factor_29months_h12']:.2f}"); mac("DecayFacNinetySix", f"{mech['decay_factor_29months_h96']:.2f}")
mac("Growth", f"{mech['growth_2025_over_2018']:.1f}"); mac("ShareTwentyFiveCorpus", f"{mech['share_2025_in_corpus']:.2f}")
mac("ShareTwentyFiveDecay", f"{mech['share_2025_in_decay12_top20']:.3f}"); mac("ShareTwentyFiveBM", f"{mech['share_2025_in_bm25_top20']:.2f}")
mac("ShareTwentyFiveRel", f"{mech['share_2025_in_relevant']:.3f}")
r, pv = num["spearman_postshare_dnDCG_DF"]; mac("RhoDF", f"{r:.2f}"); mac("RhoDFp", f"{pv:.3f}")
r, pv = num["spearman_postshare_dnDCG_Dec12"]; mac("RhoDec", f"{r:.2f}"); mac("RhoDecp", f"{pv:.2f}")
mac("NDFHelps", num["n_queries_DF_helps_nDCG"]); mac("NDFHurts", num["n_queries_DF_hurts_nDCG"])
mac("NDecHurts", num["n_queries_Dec12_hurts_nDCG"]); mac("NDecHelps", num["n_queries_Dec12_helps_nDCG"])
sens = pd.read_csv("results/table_sensitivity.csv").set_index("h")
mac("SensNinetySixRpost", f3(sens.loc["96.0", "R_post_active"] if "96.0" in sens.index else sens.loc[96.0, "R_post_active"]))
# latency
L = pd.read_csv("results/latency_summary.csv").set_index("method")
mac("LatBM", f"{L.loc['BM25','median']:.1f}"); mac("LatDec", f"{L.loc['BM25+Decay(h=12)','median']:.1f}")
mac("LatTF", f"{L.loc['TFIDF','median']:.1f}"); mac("LatRec", f"{L.loc['RecencyOnly','median']:.1f}")
mac("LatDF", f"{L.loc[f'DateFilter(T={T})','median']:.1f}")

# link to the review's severity model (analysis_growth.py)
gr = json.load(open("results/growth.json"))
mac("GrowthG", f"{gr['g_all_papers']:.3f}"); mac("GrowthRtwo", f"{gr['r2_all_papers']:.2f}")
mac("GrowthGAbs", f"{gr['g_with_abstract']:.3f}"); mac("DoublingYears", f"{gr['doubling_years_all_papers']:.1f}")
mac("GEighteen", f"{gr['G_18months_all_papers']:.2f}"); mac("GTwentyNine", f"{gr['G_29months_all_papers']:.2f}")
mac("GEighteenReview", f"{gr['G_18months_review_g0085']:.2f}")
mac("RhoTwenty", f"{gr['rho_BM25_k20']:.3f}"); mac("RhoHundred", f"{gr['rho_BM25_k100']:.3f}")
mac("NAllEighteen", f"{gr['counts_all_papers']['2018']:,}"); mac("NAllTwentyFive", f"{gr['counts_all_papers']['2025']:,}")

with open(f"{OUT}/numbers.tex", "w") as fh:
    fh.write("% AUTO-GENERATED by scripts/make_tables.py from results/*.csv -- do not edit\n")
    for k, v in macros.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{tex_signs(v)}}}\n")
print(f"{len(macros)} macros; tables in {OUT}")
