#!/usr/bin/env bash
# Runs phases 2 to 6 from the repository root.
set -e
python src/phase2_load_and_clean.py
python src/phase3_build_database.py
python src/phase4_eda_and_stats.py
python src/phase5_modelling.py
python src/phase6_build_excel.py
echo "Done. Open excel/Student_Performance_Dashboard.xlsx"
