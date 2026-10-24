"""
Phase 3: build the SQLite database and run the analysis queries.

Usage:
    python phase3_build_database.py
Needs: data/processed/students_clean.csv (from Phase 2) and sql/analysis_queries.sql
Output: student_analytics.db and reports/sql_results.txt
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

CSV = Path("data/processed/students_clean.csv")
DB = Path("student_analytics.db")
QUERIES = Path("sql/analysis_queries.sql")
RESULTS = Path("reports/sql_results.txt")
RESULTS.parent.mkdir(exist_ok=True)

df = pd.read_csv(CSV)
df.insert(0, "student_id", range(1, len(df) + 1))
df["grade_band"] = df["grade_band"].astype(str)
df["absence_band"] = df["absence_band"].astype(str)

if DB.exists():
    DB.unlink()

con = sqlite3.connect(DB)
con.executescript(Path("sql/schema.sql").read_text())
df.to_sql("students", con, if_exists="append", index=False)

n = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
print(f"Loaded {n} rows into students")

# Split the query file into named blocks: "-- name: <title>"
blocks = re.split(r"^-- name: ", QUERIES.read_text(), flags=re.M)[1:]
out = []
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)
for block in blocks:
    title, _, sql = block.partition("\n")
    res = pd.read_sql_query(sql, con)
    text = f"\n### {title.strip()}\n{res.to_string(index=False)}\n"
    print(text)
    out.append(text)

RESULTS.write_text("".join(out), encoding="utf-8")
con.close()
