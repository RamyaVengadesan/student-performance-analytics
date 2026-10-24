"""
Phase 2: load, quality-check, clean and feature-engineer the UCI Student Performance data.

Usage:
    1. Put student-mat.csv and student-por.csv in data/raw/
    2. python phase2_load_and_clean.py
Output:
    data/processed/students_clean.csv
    data/processed/quality_report.txt
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

EXPECTED_COLS = [
    "school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu",
    "Mjob", "Fjob", "reason", "guardian", "traveltime", "studytime", "failures",
    "schoolsup", "famsup", "paid", "activities", "nursery", "higher", "internet",
    "romantic", "famrel", "freetime", "goout", "Dalc", "Walc", "health",
    "absences", "G1", "G2", "G3",
]
BINARY_YN = ["schoolsup", "famsup", "paid", "activities", "nursery",
             "higher", "internet", "romantic"]

report = []


def log(msg=""):
    print(msg)
    report.append(str(msg))


def load(name, subject):
    df = pd.read_csv(RAW / name, sep=";")
    df.columns = df.columns.str.strip()
    df["subject"] = subject
    return df


mat = load("student-mat.csv", "Maths")
por = load("student-por.csv", "Portuguese")

log("=== LOAD ===")
log(f"Maths shape: {mat.shape} | Portuguese shape: {por.shape}")

# ---- Column check ----
for name, df in [("Maths", mat), ("Portuguese", por)]:
    missing_cols = set(EXPECTED_COLS) - set(df.columns)
    extra_cols = set(df.columns) - set(EXPECTED_COLS) - {"subject"}
    log(f"{name}: missing columns={sorted(missing_cols)} extra columns={sorted(extra_cols)}")

df = pd.concat([mat, por], ignore_index=True)

# ---- Quality checks ----
log("\n=== QUALITY CHECKS ===")
log(f"Combined shape: {df.shape}")
log(f"Missing values per column (non-zero only):\n{df.isna().sum()[df.isna().sum() > 0]}")
log(f"Fully duplicated rows (within the combined file): {df.duplicated().sum()}")
log("\nNumeric ranges:")
log(df[["age", "absences", "G1", "G2", "G3"]].describe().round(2))

for col in ["G1", "G2", "G3"]:
    bad = df[(df[col] < 0) | (df[col] > 20)]
    log(f"{col} outside 0-20: {len(bad)} rows")

log(f"Records with G3 == 0 (possible dropouts): {(df['G3'] == 0).sum()}")
log(f"Absences > 30 (potential outliers): {(df['absences'] > 30).sum()}")

# ---- Cleaning ----
df = df.drop_duplicates().copy()

for col in [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]:
    df[col] = df[col].astype(str).str.strip()

for col in BINARY_YN:
    df[col] = df[col].map({"yes": 1, "no": 0})

# Flag, do not delete, suspicious records
df["dropout_flag"] = (df["G3"] == 0).astype(int)
df["high_absence_flag"] = (df["absences"] > 30).astype(int)

# ---- Feature engineering ----
df["pass_flag"] = (df["G3"] >= 10).astype(int)
df["grade_band"] = pd.cut(
    df["G3"], bins=[-1, 9, 13, 16, 20],
    labels=["Fail", "Average", "Good", "Excellent"],
)
df["absence_band"] = pd.cut(
    df["absences"], bins=[-1, 0, 5, 10, np.inf],
    labels=["0", "1-5", "6-10", "11+"],
)
df["grade_change"] = df["G3"] - df["G1"]
df["avg_parent_edu"] = (df["Medu"] + df["Fedu"]) / 2
df["alc_total"] = df["Dalc"] + df["Walc"]

log("\n=== AFTER CLEANING ===")
log(f"Final shape: {df.shape}")
log(f"Pass rate by subject:\n{df.groupby('subject')['pass_flag'].mean().round(3)}")
log(f"Grade band counts:\n{df['grade_band'].value_counts()}")
log(f"Correlation of absences with G3: {df['absences'].corr(df['G3']):.3f}")

df.to_csv(OUT / "students_clean.csv", index=False)
(OUT / "quality_report.txt").write_text("\n".join(report), encoding="utf-8")
log(f"\nSaved: {OUT / 'students_clean.csv'}")
