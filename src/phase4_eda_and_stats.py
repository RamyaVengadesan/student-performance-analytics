"""
Phase 4: exploratory data analysis and statistical tests.

Usage:  python phase4_eda_and_stats.py
Needs:  data/processed/students_clean.csv
Output: reports/charts/*.png and reports/stats_results.txt
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

CHARTS = Path("reports/charts")
CHARTS.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", context="notebook")
PALETTE = {"Maths": "#2563eb", "Portuguese": "#f59e0b"}

df = pd.read_csv("data/processed/students_clean.csv")
active = df[df["dropout_flag"] == 0].copy()   # excludes G3 == 0 records
out = []


def log(text=""):
    print(text)
    out.append(str(text))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values (keeps the original order)."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def cramers_v(table):
    chi2 = stats.chi2_contingency(table, correction=False)[0]
    n = table.to_numpy().sum()
    r, k = table.shape
    return np.sqrt(chi2 / (n * (min(r, k) - 1)))


def cohens_d(a, b):
    na, nb = len(a), len(b)
    pooled = np.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    return (a.mean() - b.mean()) / pooled


# ------------------------------------------------------------------ charts
# 1. Grade distribution by subject
fig, ax = plt.subplots(figsize=(8, 4.5))
sns.histplot(data=df, x="G3", hue="subject", bins=21, binrange=(0, 21), multiple="dodge",
             palette=PALETTE, shrink=0.85, ax=ax)
ax.axvline(9.5, color="#dc2626", ls="--", lw=1.2)
ax.text(9.6, ax.get_ylim()[1] * 0.92, "pass mark (10)", color="#dc2626", fontsize=9)
ax.set(title="Final grade (G3) distribution by subject", xlabel="G3 (0-20)", ylabel="Students")
fig.tight_layout(); fig.savefig(CHARTS / "01_grade_distribution.png", dpi=150); plt.close(fig)

# 2. Absences vs G3 (dropout records excluded)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
sns.regplot(data=active, x="absences", y="G3", scatter_kws={"alpha": 0.35, "s": 18},
            line_kws={"color": "#dc2626"}, ax=axes[0])
axes[0].set(title="Absences vs final grade", xlabel="Absences", ylabel="G3")
order = ["0", "1-5", "6-10", "11+"]
sns.boxplot(data=active, x="absence_band", y="G3", order=order, color="#93c5fd", ax=axes[1])
axes[1].set(title="Final grade by absence band", xlabel="Absence band", ylabel="G3")
fig.tight_layout(); fig.savefig(CHARTS / "02_absences_vs_grade.png", dpi=150); plt.close(fig)

# 3. Correlation heatmap (Spearman)
num_cols = ["age", "Medu", "Fedu", "traveltime", "studytime", "failures", "famrel",
            "freetime", "goout", "Dalc", "Walc", "health", "absences", "G1", "G2", "G3"]
corr = active[num_cols].corr(method="spearman")
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr, cmap="RdBu_r", center=0, annot=True, fmt=".2f", annot_kws={"size": 7},
            cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_title("Spearman correlation (dropout records excluded)")
fig.tight_layout(); fig.savefig(CHARTS / "03_correlation_heatmap.png", dpi=150); plt.close(fig)

# 4. Pass rate by key risk factors
factors = [("failures", "Past failures"), ("higher", "Wants higher edu (1=yes)"),
           ("absence_band", "Absence band"), ("studytime", "Study time level")]
fig, axes = plt.subplots(2, 2, figsize=(11, 8))
for ax, (col, title) in zip(axes.ravel(), factors):
    data = df if col != "absence_band" else active
    order_ = order if col == "absence_band" else None
    rate = (data.groupby(col)["pass_flag"].mean() * 100)
    if order_:
        rate = rate.reindex(order_)
    ax.bar(rate.index.astype(str), rate.values, color="#2563eb")
    ax.set(title=title, ylabel="Pass rate (%)", ylim=(0, 100))
    for i, v in enumerate(rate.values):
        ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=9)
fig.suptitle("Pass rate (G3 >= 10) by key factors", y=1.0)
fig.tight_layout(); fig.savefig(CHARTS / "04_pass_rate_factors.png", dpi=150); plt.close(fig)

# 5. Grade progression G1 -> G2 -> G3
prog = df.groupby("subject")[["G1", "G2", "G3"]].mean().T
fig, ax = plt.subplots(figsize=(7, 4.5))
for subj in prog.columns:
    ax.plot(prog.index, prog[subj], marker="o", lw=2, label=subj, color=PALETTE[subj])
ax.set(title="Average grade across the three periods", ylabel="Average grade", ylim=(9, 13))
ax.legend()
fig.tight_layout(); fig.savefig(CHARTS / "05_grade_progression.png", dpi=150); plt.close(fig)

# 6. Urban/rural x internet
fig, ax = plt.subplots(figsize=(7, 4.5))
tmp = active.assign(internet_access=active["internet"].map({1: "Internet", 0: "No internet"}))
sns.barplot(data=tmp, x="address", y="G3", hue="internet_access", errorbar=("ci", 95),
            palette=["#2563eb", "#9ca3af"], order=["U", "R"], ax=ax)
ax.set(title="Final grade by address and internet access (95% CI)", xlabel="Address (U=urban, R=rural)")
fig.tight_layout(); fig.savefig(CHARTS / "06_address_internet.png", dpi=150); plt.close(fig)

# ------------------------------------------------------------------ tests
log("=== DATA USED ===")
log(f"All students: {len(df)} | Active (G3 > 0, dropout records excluded): {len(active)}")

log("\n=== 1. SUBJECT DIFFERENCE IN FINAL GRADE (Welch t-test, all students) ===")
m = df.loc[df.subject == "Maths", "G3"]; p_ = df.loc[df.subject == "Portuguese", "G3"]
t, p = stats.ttest_ind(m, p_, equal_var=False)
log(f"Maths mean {m.mean():.2f} vs Portuguese mean {p_.mean():.2f} | t={t:.2f}, p={p:.2e}, "
    f"Cohen's d={cohens_d(m, p_):.2f}")

log("\n=== 2. CORRELATIONS WITH FINAL GRADE G3 (Spearman, active students) ===")
rows = []
for c in [c for c in num_cols if c != "G3"]:
    rho, pv = stats.spearmanr(active[c], active["G3"])
    rows.append((c, rho, pv))
corr_df = pd.DataFrame(rows, columns=["feature", "rho", "p"])
corr_df["p_holm"] = holm(corr_df["p"])
corr_df["significant"] = corr_df["p_holm"] < 0.05
corr_df = corr_df.reindex(corr_df.rho.abs().sort_values(ascending=False).index)
log(corr_df.round(4).to_string(index=False))

log("\n=== 3. ABSENCE BANDS (Kruskal-Wallis, active students) ===")
groups = [active.loc[active.absence_band == b, "G3"] for b in order]
h, p = stats.kruskal(*groups)
log(f"H={h:.2f}, p={p:.2e}")
rho, pv = stats.spearmanr(active["absences"], active["G3"])
log(f"Spearman absences vs G3: rho={rho:.3f}, p={pv:.2e}")

log("\n=== 4. CHI-SQUARE TESTS ON PASS/FAIL (all students) ===")
tests = {
    "Wants higher education": "higher",
    "Has past failures (any)": None,
    "Urban vs rural": "address",
    "Internet at home": "internet",
    "School support": "schoolsup",
    "Sex": "sex",
    "Romantic relationship": "romantic",
}
rows = []
for label, col in tests.items():
    series = (df["failures"] > 0).astype(int) if col is None else df[col]
    table = pd.crosstab(series, df["pass_flag"])
    chi2, pv, _, _ = stats.chi2_contingency(table)
    rows.append((label, chi2, pv, cramers_v(table)))
chi_df = pd.DataFrame(rows, columns=["factor", "chi2", "p", "cramers_v"])
chi_df["p_holm"] = holm(chi_df["p"])
chi_df["significant"] = chi_df["p_holm"] < 0.05
log(chi_df.round(4).to_string(index=False))

log("\n=== 5. INTERNET ACCESS WITHIN URBAN AND RURAL (Mann-Whitney, active students) ===")
for addr in ["U", "R"]:
    sub = active[active.address == addr]
    a = sub.loc[sub.internet == 1, "G3"]; b = sub.loc[sub.internet == 0, "G3"]
    u, pv = stats.mannwhitneyu(a, b, alternative="two-sided")
    log(f"{addr}: internet mean {a.mean():.2f} (n={len(a)}) vs none {b.mean():.2f} (n={len(b)}) | "
        f"p={pv:.4f}, d={cohens_d(a, b):.2f}")

log("\n=== 6. STUDY TIME: LEVEL AND GRADE CHANGE (Kruskal-Wallis, active students) ===")
for target in ["G3", "grade_change"]:
    groups = [active.loc[active.studytime == s, target] for s in sorted(active.studytime.unique())]
    h, pv = stats.kruskal(*groups)
    log(f"{target} across study-time levels: H={h:.2f}, p={pv:.4f}")

log("\n=== 7. PARENT EDUCATION (Spearman with G3, active students) ===")
rho, pv = stats.spearmanr(active["avg_parent_edu"], active["G3"])
log(f"avg_parent_edu vs G3: rho={rho:.3f}, p={pv:.2e}")

log("\n=== 8. HOW MUCH DOES G2 EXPLAIN? (squared Pearson, all students) ===")
for col in ["G1", "G2"]:
    r = df[col].corr(df["G3"])
    log(f"{col} vs G3: r={r:.3f}, R^2={r**2:.3f}")

Path("reports/stats_results.txt").write_text("\n".join(out), encoding="utf-8")
print("\nSaved charts and reports/stats_results.txt")
