# Insights Report: Student Performance & Attendance Analytics

**Data:** UCI Student Performance dataset (Cortez & Silva, 2008), 1,044 records from two Portuguese secondary schools (395 Maths, 649 Portuguese)
**Methods:** Python (Pandas, NumPy, SciPy, scikit-learn), SQL (SQLite), Excel, Power BI guide
**Pass definition:** final grade G3 of 10 or more (scale 0-20)
**Unit of analysis:** one row is one student-subject record. The 1,044 records are not 1,044 different people, because some students appear in both subject files and there is no student ID. "Students" in the text below means students in a given record group.

## 1. Executive summary

Overall 78.0% of records pass. Three things stand out:

1. **Past failures are the strongest warning sign.** Students with no past failures pass 85.0% of the time. With one past failure the pass rate drops to 51.7%, and with three it is 30.0%.
2. **Absences matter, but modestly.** The pass rate falls from 89.9% (no absences) to 63.5% for students with 11 or more absences.
3. **The first-period grade is the best early predictor.** A model using only G1 plus background factors identifies likely failures well (ROC-AUC 0.93, validated with folds that keep a student's two subject rows together). Students it marks High risk fail about 72% of the time, against 5% for Low risk.

## 2. Data and quality

- 33 original columns, no missing values and no duplicate rows.
- 53 records have a final grade of 0. All 53 show 0 absences, so attendance was probably never recorded for them. They were flagged as possible dropouts (a label for further checking, not a confirmed outcome) and excluded from attendance analysis (991 "active" records remain). Including them hides the absence effect (overall correlation -0.05, versus -0.22 once excluded).
- 6 records have more than 30 absences (maximum 75, in Maths). They were kept and flagged.
- The two subject files overlap: many students appear in both, so rows are not fully independent. There is no student ID. Matching on 13 background attributes (the key suggested by the dataset authors) gives 382 row pairs, but they come from only 366 distinct attribute combinations, and 358 pairs are strictly one-to-one. Cross-subject numbers below use those 358 and are approximate.

## 3. Findings

### 3.1 Subjects
| | Maths | Portuguese |
|---|---|---|
| Records | 395 | 649 |
| Average final grade | 10.42 | 11.91 |
| Pass rate | 67.1% | 84.6% |

The gap is statistically significant (Welch t-test, p < 0.001) with a small-to-medium effect (Cohen's d = -0.39). Of the 358 students matched one-to-one (approximate), 96 passed Portuguese but failed Maths, and only 7 did the reverse.

### 3.2 Attendance (active records)
| Absences | Records | Avg G3 | Pass rate |
|---|---|---|---|
| 0 | 306 | 12.77 | 89.9% |
| 1-5 | 368 | 11.91 | 83.4% |
| 6-10 | 202 | 11.67 | 78.7% |
| 11+ | 115 | 10.37 | 63.5% |

Absences and the final grade are negatively correlated (Spearman rho = -0.24, p < 0.001), and the bands differ significantly (Kruskal-Wallis, p < 0.001).

### 3.3 Past failures and aspiration
| Past failures | Records | Pass rate |
|---|---|---|
| 0 | 861 | 85.0% |
| 1 | 120 | 51.7% |
| 2 | 33 | 33.3% |
| 3 | 30 | 30.0% |

Having any past failure has the largest association with failing (Cramér's V = 0.37). Students who want higher education pass at 80.7%, against 48.3% for those who do not (V = 0.22).

### 3.4 Family background and access
- Parent education is positively related to grades (rho = 0.23). Pass rates rise from 71.3% (low) to 83.3% (high parent education).
- Internet access is linked to higher grades only for urban students: 12.34 with internet against 11.11 without (d = 0.42, p < 0.001). Rural students show no difference (11.31 against 11.58, p = 0.45). This is a lead to investigate, not a proven effect, and the urban group without internet is small (114 students).

### 3.5 Study habits
More weekly study time goes with higher final grades (p < 0.001), but not with larger improvement from G1 to G3 (p = 0.60). Students who study more tend to start ahead and stay ahead.

### 3.6 Other factors
Weekday and weekend alcohol use have weak negative correlations with grades (about -0.18). Sex, school support and having internet overall were not significant for pass/fail after correcting for multiple tests.

## 4. Predictive modelling

Models were evaluated with 5-fold cross-validation repeated 3 times, against a baseline that always predicts "pass" (78.0% accuracy). Because the same student can appear in both subject files, folds are **grouped**: rows with the same 13 background attributes always stay in the same fold, so a student's Maths row is never in training while their Portuguese row is in testing. Ordinary row-level folds gave almost identical results (scenario B ROC-AUC 0.93 either way), so this overlap did not noticeably inflate the scores here. Grouping by attributes is itself approximate, so the results still need testing on new data.

| Scenario | Pass/fail ROC-AUC | Accuracy | Final grade MAE |
|---|---|---|---|
| A: G1 and G2 known | 0.97 | about 92% | 0.89 |
| B: only G1 known | 0.93 | about 87% | 1.39 |
| C: no grades | 0.77-0.80 | about 79-80% | 2.34 |

- Scenario A mostly reflects that the second-period grade almost determines the final one (G2 explains about 83% of the variance in G3).
- Scenario B is the practical early-warning model. G1 dominates its importance ranking, followed by past failures and subject.
- Scenario C shows that background factors alone add little beyond the baseline on accuracy, though they rank students better than chance.

**Risk groups (scenario B, grouped out-of-fold scores):**

| Risk level | Records | Actual fail rate |
|---|---|---|
| Low (<20%) | 713 | 5.0% |
| Medium (20-50%) | 124 | 37.1% |
| High (>50%) | 207 | 71.5% |

## 5. Recommendations

These follow from the associations above and should be tested before being treated as proven.

1. **Check early.** After the first period, review the High-risk list (about 20% of records) and offer support before grades fall further.
2. **Watch attendance around 10 absences.** The pass rate drops sharply in the 11+ group, so a trigger near that level is a sensible starting point.
3. **Prioritise students with past failures.** Their pass rates are between 30% and 52%.
4. **Strengthen Maths support.** The Maths pass rate is 17.5 points below Portuguese.
5. **Record attendance for everyone.** The 53 records with no attendance data limit what can be learned about dropouts.
6. **Test the internet-access lead.** If urban students without internet are falling behind, a small trial of access support could confirm it.
7. **Use scores as a prompt, not a label.** A risk score should start a conversation with the student, not decide anything about them.

## 6. Limitations

- Observational data: results show associations, not causes.
- The data are from two schools in Portugal in 2005-2006, so they may not transfer to other settings.
- Students appear in both subject files and there is no student ID, so cross-subject matching and the grouped validation both rely on approximate attribute matching.
- G3 = 0 records may mix dropouts and missing data.
- The model was validated only inside this dataset (grouped cross-validation) and has not been tested on new data.
- Some groups are small (for example, 30 records with 3 past failures).

## 7. Source

P. Cortez and A. Silva. *Using Data Mining to Predict Secondary School Student Performance.* In Proceedings of the 5th FUture BUsiness TEChnology Conference (FUBUTEC 2008), pp. 5-12, Porto, Portugal, April 2008, EUROSIS. UCI Machine Learning Repository, licensed CC BY 4.0.
