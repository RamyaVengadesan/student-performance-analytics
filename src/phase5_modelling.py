"""
Phase 5: predictive modelling (scikit-learn).

Two tasks, each tested in three scenarios that differ in which grades are available:
  A  all grades known (G1 and G2)          -> upper bound, mostly "predicts from the past grade"
  B  only the first-period grade G1 known   -> realistic early-warning model
  C  no grades at all                       -> background and behaviour factors only

Validation: the Maths and Portuguese files contain many of the same students, and there is no
student id. Plain row-level cross-validation can put one student's Maths row in training and their
Portuguese row in testing. So every reported result uses grouped folds: rows that share the same
13 background attributes (the matching key suggested by the dataset authors) are kept together.
Row-level results are also printed, for comparison only.

Usage:  python phase5_modelling.py
Needs:  data/processed/students_clean.csv
Output: reports/model_results.txt, reports/charts/07-08*.png,
        data/processed/student_risk_scores.csv, models/early_warning_model.joblib
"""
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (GradientBoostingClassifier, GradientBoostingRegressor,
                              RandomForestClassifier, RandomForestRegressor)
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import (RepeatedStratifiedKFold, StratifiedGroupKFold,
                                     cross_validate, cross_val_predict)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SEED = 42
CHARTS = Path("reports/charts"); CHARTS.mkdir(parents=True, exist_ok=True)
Path("models").mkdir(exist_ok=True)
sns.set_theme(style="whitegrid")

df = pd.read_csv("data/processed/students_clean.csv")
df.insert(0, "student_id", range(1, len(df) + 1))      # same ids as the SQLite database

# Columns derived from the target (or from G3) would leak the answer, so they never go in.
LEAK = ["G3", "pass_flag", "grade_band", "grade_change", "dropout_flag"]
REDUNDANT = ["absence_band", "high_absence_flag", "avg_parent_edu", "alc_total", "student_id"]
base = df.drop(columns=LEAK + REDUNDANT)

SCENARIOS = {
    "A: G1 + G2 known": list(base.columns),
    "B: only G1 known": [c for c in base.columns if c != "G2"],
    "C: no grades": [c for c in base.columns if c not in ("G1", "G2")],
}
y_cls = df["pass_flag"]
y_reg = df["G3"]

MATCH_KEYS = ["school", "sex", "age", "address", "famsize", "Pstatus", "Medu", "Fedu",
              "Mjob", "Fjob", "reason", "nursery", "internet"]
groups = df.groupby(MATCH_KEYS).ngroup()
print(f"{len(df)} rows -> {groups.nunique()} groups (rows sharing a key stay in the same fold)")


def grouped_splits(n_repeats=3):
    """5-fold grouped, class-stratified splits, repeated with different shuffles."""
    out_ = []
    for rep in range(n_repeats):
        sgk = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED + rep)
        out_.extend(list(sgk.split(base, y_cls, groups)))
    return out_


GROUPED = grouped_splits()

out = []
def log(t=""):
    print(t); out.append(str(t))


def preprocessor(cols, scale):
    cat = [c for c in cols if not pd.api.types.is_numeric_dtype(base[c])]
    num = [c for c in cols if c not in cat]
    return ColumnTransformer([
        ("num", StandardScaler() if scale else "passthrough", num),
        ("cat", OneHotEncoder(handle_unknown="ignore", drop="if_binary"), cat),
    ])


def cls_models(cols):
    return {
        "Baseline (majority)": Pipeline([("p", preprocessor(cols, False)), ("m", DummyClassifier(strategy="most_frequent"))]),
        "Logistic Regression": Pipeline([("p", preprocessor(cols, True)), ("m", LogisticRegression(max_iter=2000))]),
        "Random Forest": Pipeline([("p", preprocessor(cols, False)),
                                   ("m", RandomForestClassifier(n_estimators=300, min_samples_leaf=3, random_state=SEED, n_jobs=-1))]),
        "Gradient Boosting": Pipeline([("p", preprocessor(cols, False)),
                                       ("m", GradientBoostingClassifier(random_state=SEED))]),
    }


def reg_models(cols):
    return {
        "Baseline (mean)": Pipeline([("p", preprocessor(cols, False)), ("m", DummyRegressor())]),
        "Ridge": Pipeline([("p", preprocessor(cols, True)), ("m", Ridge(alpha=10))]),
        "Random Forest": Pipeline([("p", preprocessor(cols, False)),
                                   ("m", RandomForestRegressor(n_estimators=300, min_samples_leaf=3, random_state=SEED, n_jobs=-1))]),
        "Gradient Boosting": Pipeline([("p", preprocessor(cols, False)),
                                       ("m", GradientBoostingRegressor(random_state=SEED))]),
    }


# ---------------------------------------------------------------- classification
log("=== PASS / FAIL CLASSIFICATION (5-fold x 3 repeats, all 1,044 students) ===")
log(f"Pass rate (class balance): {y_cls.mean():.1%}")
log("Main results use GROUPED folds (same-student rows kept together). Row-level shown for comparison.")
cv_rowlevel = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
cls_rows = []
for scen, cols in SCENARIOS.items():
    X = base[cols]
    for name, model in cls_models(cols).items():
        for vname, cv_ in [("grouped", GROUPED), ("row-level", cv_rowlevel)]:
            r = cross_validate(model, X, y_cls, cv=cv_, n_jobs=1,
                               scoring=["accuracy", "f1_macro", "roc_auc"])
            cls_rows.append({"scenario": scen, "model": name, "validation": vname,
                             "accuracy": r["test_accuracy"].mean(), "acc_sd": r["test_accuracy"].std(),
                             "f1_macro": r["test_f1_macro"].mean(), "roc_auc": r["test_roc_auc"].mean()})
cls_all = pd.DataFrame(cls_rows)
cls_df = cls_all[cls_all.validation == "grouped"].drop(columns="validation").reset_index(drop=True)
log("\nGROUPED validation (reported):")
log(cls_df.round(3).to_string(index=False))
log("\nRow-level validation (comparison only, optimistic):")
log(cls_all[cls_all.validation == "row-level"].drop(columns="validation").round(3).to_string(index=False))

# ---------------------------------------------------------------- regression
log("\n=== FINAL GRADE REGRESSION (grouped 5-fold x 3 repeats) ===")
reg_rows = []
for scen, cols in SCENARIOS.items():
    X = base[cols]
    for name, model in reg_models(cols).items():
        r = cross_validate(model, X, y_reg, cv=GROUPED, n_jobs=1,
                           scoring=["neg_mean_absolute_error", "neg_root_mean_squared_error", "r2"])
        reg_rows.append({"scenario": scen, "model": name,
                         "MAE": -r["test_neg_mean_absolute_error"].mean(),
                         "RMSE": -r["test_neg_root_mean_squared_error"].mean(),
                         "R2": r["test_r2"].mean()})
reg_df = pd.DataFrame(reg_rows)
log(reg_df.round(3).to_string(index=False))

# ---------------------------------------------------------------- charts: comparison
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
sns.barplot(data=cls_df, x="scenario", y="roc_auc", hue="model", ax=axes[0])
axes[0].set(title="Pass/fail: ROC-AUC (higher is better)", ylim=(0.4, 1.0), xlabel="", ylabel="ROC-AUC")
axes[0].axhline(0.5, color="grey", ls=":", lw=1)
sns.barplot(data=reg_df, x="scenario", y="MAE", hue="model", ax=axes[1])
axes[1].set(title="Final grade: MAE in grade points (lower is better)", xlabel="", ylabel="MAE")
axes[1].legend(fontsize=8)
axes[0].legend(fontsize=8, loc="lower right")
fig.tight_layout(); fig.savefig(CHARTS / "07_model_comparison.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- permutation importance
def importance_plot(scen, ax):
    cols = SCENARIOS[scen]
    tr, te = GROUPED[0]                      # first grouped fold = hold-out set (about 20%)
    X_tr, X_te, y_tr, y_te = base[cols].iloc[tr], base[cols].iloc[te], y_cls.iloc[tr], y_cls.iloc[te]
    model = cls_models(cols)["Random Forest"].fit(X_tr, y_tr)
    pi = permutation_importance(model, X_te, y_te, scoring="roc_auc", n_repeats=30, random_state=SEED)
    imp = pd.Series(pi.importances_mean, index=cols).sort_values(ascending=False).head(10)
    sd = pd.Series(pi.importances_std, index=cols)[imp.index]
    ax.barh(imp.index[::-1], imp.values[::-1], xerr=sd.values[::-1], color="#2563eb")
    ax.set(title=f"Scenario {scen}", xlabel="Drop in ROC-AUC when shuffled")
    return imp

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
log("\n=== PERMUTATION IMPORTANCE (Random Forest, grouped hold-out fold, top 10) ===")
for ax, scen in zip(axes, ["B: only G1 known", "C: no grades"]):
    imp = importance_plot(scen, ax)
    log(f"\n{scen}\n{imp.round(4).to_string()}")
fig.suptitle("What drives the pass/fail prediction", y=1.0)
fig.tight_layout(); fig.savefig(CHARTS / "08_feature_importance.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------- early-warning model + risk scores
best_name = "Logistic Regression" if (
    cls_df.query("scenario == 'B: only G1 known' and model == 'Logistic Regression'")["roc_auc"].iloc[0]
    >= cls_df.query("scenario == 'B: only G1 known' and model == 'Random Forest'")["roc_auc"].iloc[0]
) else "Random Forest"
cols_b = SCENARIOS["B: only G1 known"]
final = cls_models(cols_b)[best_name]
oof = cross_val_predict(final, base[cols_b], y_cls, cv=GROUPED[:5], method="predict_proba")[:, 0]
risk = pd.DataFrame({"student_id": df["student_id"], "subject": df["subject"], "school": df["school"],
                     "G1": df["G1"], "absences": df["absences"], "failures": df["failures"],
                     "actual_pass": y_cls, "risk_of_failing": oof.round(3)})
risk["risk_level"] = pd.cut(risk["risk_of_failing"], [-0.01, 0.2, 0.5, 1.0], labels=["Low", "Medium", "High"])
risk.to_csv("data/processed/student_risk_scores.csv", index=False)
final.fit(base[cols_b], y_cls)
joblib.dump({"model": final, "columns": cols_b}, "models/early_warning_model.joblib")

log(f"\n=== EARLY-WARNING MODEL (scenario B, {best_name}) ===")
log("Risk scores are out-of-fold with grouped folds: a student is scored by a model that never saw their rows.")
log(risk.groupby("risk_level", observed=True).agg(students=("student_id", "count"),
                                                  actual_fail_rate=("actual_pass", lambda s: 1 - s.mean())).round(3).to_string())

Path("reports/model_results.txt").write_text("\n".join(out), encoding="utf-8")
