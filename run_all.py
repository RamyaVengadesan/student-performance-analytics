"""Runs phases 2 to 6 in order. Works on Windows, macOS and Linux.

Usage (from anywhere):  python run_all.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # the scripts use paths relative to the repository root

SCRIPTS = [
    "src/phase2_load_and_clean.py",
    "src/phase3_build_database.py",
    "src/phase4_eda_and_stats.py",
    "src/phase5_modelling.py",
    "src/phase6_build_excel.py",
]

for script in SCRIPTS:
    print(f"\n=== Running {script} ===")
    subprocess.run([sys.executable, script], check=True)

print("\nDone. Open excel/Student_Performance_Dashboard.xlsx")
