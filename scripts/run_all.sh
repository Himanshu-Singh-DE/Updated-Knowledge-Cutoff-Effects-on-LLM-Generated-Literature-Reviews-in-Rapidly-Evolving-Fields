#!/usr/bin/env bash
# Full pipeline: data -> labels -> validation -> retrieval -> selection -> evaluation -> figures/tables -> PDF.
# Usage: bash scripts/run_all.sh [DATA_RAW]   (DATA_RAW holds acl/ and lists/ from fetch_data.sh)
set -euo pipefail
RAW=${1:-../data_raw}
mkdir -p results/logs
python3 src/build_corpus.py --xml_dir "$RAW/acl/data/xml" --out data/documents.csv
python3 src/match_lists.py --lists_dir "$RAW/lists" --lists_config configs/lists.json --out data/list_matches.csv > results/match_summary.txt
python3 src/build_labels.py
python3 src/build_labels.py --cutoff 2022-07-01
python3 src/build_labels.py --cutoff 2024-07-01
python3 scripts/validate_baseline.py | tee results/logs/03_baseline_validation.log
python3 scripts/run_retrieval.py --save_k 1000 | tee results/logs/09_run_retrieval_depth1000.log
python3 scripts/select_h.py | tee results/logs/07_select_h_tuning.log
python3 scripts/evaluate_all.py | tee results/logs/10_evaluate_test.log
python3 scripts/analysis_mechanism.py | tee results/logs/11_failure_mechanism.log
python3 scripts/analysis_growth.py --xml_dir "$RAW/acl/data/xml" | tee results/logs/13_growth_rate_vs_review.log
python3 scripts/make_figures.py
python3 scripts/make_tables.py
echo "Now compile paper/main.tex (Overleaf, or: cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main)"
