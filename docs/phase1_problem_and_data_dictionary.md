# Student Performance & Attendance Analytics

**Dataset:** UCI Student Performance (Cortez & Silva, 2008), CC BY 4.0
**Stack:** Python, Pandas, NumPy, SQL, Power BI, Excel (scikit-learn for the optional modelling phase)

## Phase 1: Problem definition

**Goal:** Understand which attendance, study and background factors are linked to student grades, and flag students who need early support.

**Business questions**
1. How are absences related to the final grade (G3)?
2. Do grades improve or decline from G1 to G3, and who improves most?
3. Which study habits (study time, past failures, school support, wish for higher education) matter most?
4. Do family and background factors (parent education, address type, internet access) show a gap in results?
5. Can we predict pass/fail (G3 >= 10) early, using only G1, G2 and non-grade factors?
6. Do Maths and Portuguese results differ for the same students?

**Success output:** cleaned dataset, SQL analysis queries, statistical findings, a Power BI dashboard and a written insights report.

**Unit of analysis:** each row is one student-subject record. A student who took both subjects has two rows, and there is no student id, so 1,044 records are not 1,044 unique people.

## Data files

| File | Rows (per UCI) | Subject |
|---|---|---|
| student-mat.csv | 395 | Mathematics |
| student-por.csv | 649 | Portuguese |

Both files are semicolon-separated (`sep=";"`). The two files share 30 identical columns plus the three grade columns, which are subject-specific.

## Data dictionary (33 columns)

| Column | Type | Meaning |
|---|---|---|
| school | binary | GP (Gabriel Pereira) or MS (Mousinho da Silveira) |
| sex | binary | F or M |
| age | numeric | 15 to 22 |
| address | binary | U (urban) or R (rural) |
| famsize | binary | LE3 (3 or fewer) or GT3 (more than 3) |
| Pstatus | binary | Parents living together (T) or apart (A) |
| Medu / Fedu | ordinal 0-4 | Mother's / father's education level |
| Mjob / Fjob | nominal | Mother's / father's job category |
| reason | nominal | Reason for choosing the school |
| guardian | nominal | mother, father or other |
| traveltime | ordinal 1-4 | Home to school travel time |
| studytime | ordinal 1-4 | Weekly study time |
| failures | numeric | Past class failures |
| schoolsup / famsup | binary | Extra school / family educational support |
| paid | binary | Paid extra classes in the subject |
| activities | binary | Extra-curricular activities |
| nursery | binary | Attended nursery school |
| higher | binary | Wants to pursue higher education |
| internet | binary | Internet access at home |
| romantic | binary | In a romantic relationship |
| famrel | ordinal 1-5 | Quality of family relationships |
| freetime | ordinal 1-5 | Free time after school |
| goout | ordinal 1-5 | Going out with friends |
| Dalc / Walc | ordinal 1-5 | Workday / weekend alcohol consumption |
| health | ordinal 1-5 | Current health status |
| absences | numeric | School absences (0 to 75 observed in this file) |
| G1, G2 | numeric 0-20 | First and second period grades |
| G3 | numeric 0-20 | Final grade (target) |

*Verify these against the real file in Phase 2; the script checks the column list automatically.*

## Planned derived features (Phase 2)

- `subject`: Maths or Portuguese (added when stacking the two files)
- `pass_flag`: G3 >= 10
- `grade_band`: Fail (<10), Average (10-13), Good (14-16), Excellent (17-20)
- `absence_band`: 0, 1-5, 6-10, 11+
- `grade_change`: G3 minus G1
- `avg_parent_edu`: mean of Medu and Fedu
- `alc_total`: Dalc plus Walc

## Notes and cautions

- G3 is strongly correlated with G1 and G2. Predicting G3 without them is harder but more useful, so the modelling phase will test both.
- Students with G3 = 0 are often dropouts or non-attendees, so they are flagged rather than silently removed.
- Many students appear in both subject files. UCI suggests matching them on school, sex, age, address, famsize, Pstatus, Medu, Fedu, Mjob, Fjob, reason, nursery and internet. There is no student ID and the key is not unique (the join gives 382 row pairs from 366 distinct combinations; 358 are strictly one-to-one), so treat any cross-subject match as approximate.
- Cite the source: P. Cortez and A. Silva, *Using Data Mining to Predict Secondary School Student Performance*, 2008.

## Repository structure

```
student-performance-analytics/
  data/raw/            original UCI files (unchanged)
  data/processed/      cleaned data, risk scores, Power BI table
  src/                 one script per phase (phase2 to phase6)
  sql/                 schema and analysis queries
  reports/             insights report, results, charts
  excel/               formula-driven Excel dashboard
  powerbi/             DAX measures, theme, build guide
  models/              saved early-warning model
  docs/                this document
  run_all.py / .sh     run phases 2 to 6 in order
  README.md
```

## Phase roadmap

1. Problem definition (this file, done)
2. Load, quality check and cleaning
3. SQL layer (MySQL or SQLite)
4. EDA and statistical tests
5. Predictive modelling (optional)
6. Power BI and Excel dashboards
7. Insights report and GitHub README
