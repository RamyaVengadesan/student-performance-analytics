-- name: Q1 Overview by subject
SELECT subject,
       COUNT(*)                          AS records,
       ROUND(AVG(G1),2)                  AS avg_g1,
       ROUND(AVG(G2),2)                  AS avg_g2,
       ROUND(AVG(G3),2)                  AS avg_g3,
       ROUND(100.0*AVG(pass_flag),1)     AS pass_rate_pct,
       ROUND(AVG(absences),2)            AS avg_absences
FROM students
GROUP BY subject;

-- name: Q2 Absence band vs final grade (dropout records excluded)
SELECT absence_band,
       COUNT(*)              AS records,
       ROUND(AVG(G3),2)      AS avg_g3,
       ROUND(100.0*AVG(pass_flag),1) AS pass_rate_pct
FROM students
WHERE dropout_flag = 0
GROUP BY absence_band
ORDER BY CASE absence_band WHEN '0' THEN 1 WHEN '1-5' THEN 2 WHEN '6-10' THEN 3 ELSE 4 END;

-- name: Q3 Study time vs average grade change (G3 minus G1)
SELECT studytime,
       COUNT(*)                   AS records,
       ROUND(AVG(grade_change),2) AS avg_grade_change,
       ROUND(AVG(G3),2)           AS avg_g3
FROM students
WHERE dropout_flag = 0
GROUP BY studytime
ORDER BY studytime;

-- name: Q4 Past failures vs pass rate
SELECT failures,
       COUNT(*)                      AS records,
       ROUND(100.0*AVG(pass_flag),1) AS pass_rate_pct,
       ROUND(AVG(G3),2)              AS avg_g3
FROM students
GROUP BY failures
ORDER BY failures;

-- name: Q5 Wants higher education vs results
SELECT CASE higher WHEN 1 THEN 'Yes' ELSE 'No' END AS wants_higher_edu,
       COUNT(*)                      AS records,
       ROUND(AVG(G3),2)              AS avg_g3,
       ROUND(100.0*AVG(pass_flag),1) AS pass_rate_pct
FROM students
GROUP BY higher;

-- name: Q6 Parent education vs pass rate
SELECT CASE WHEN avg_parent_edu < 2 THEN '1 Low (<2)'
            WHEN avg_parent_edu < 3 THEN '2 Medium (2-2.9)'
            ELSE '3 High (3+)' END     AS parent_edu_level,
       COUNT(*)                        AS records,
       ROUND(AVG(G3),2)                AS avg_g3,
       ROUND(100.0*AVG(pass_flag),1)   AS pass_rate_pct
FROM students
GROUP BY parent_edu_level
ORDER BY parent_edu_level;

-- name: Q7 Urban vs rural and internet access
SELECT address,
       CASE internet WHEN 1 THEN 'Internet' ELSE 'No internet' END AS internet_access,
       COUNT(*)         AS records,
       ROUND(AVG(G3),2) AS avg_g3
FROM students
GROUP BY address, internet
ORDER BY address, internet;

-- name: Q8 Alcohol consumption vs grade
SELECT alc_total,
       COUNT(*)         AS records,
       ROUND(AVG(G3),2) AS avg_g3
FROM students
WHERE dropout_flag = 0
GROUP BY alc_total
HAVING COUNT(*) >= 20
ORDER BY alc_total;

-- name: Q9 Top 3 records per subject and school (window function)
WITH ranked AS (
    SELECT student_id, subject, school, G3, absences,
           ROW_NUMBER() OVER (PARTITION BY subject, school
                              ORDER BY G3 DESC, absences ASC, student_id) AS rank_in_group
    FROM students
)
SELECT * FROM ranked WHERE rank_in_group <= 3
ORDER BY subject, school, rank_in_group;

-- name: Q10 Records far below their subject average (window average, top 8)
SELECT student_id, subject, G3,
       ROUND(AVG(G3) OVER (PARTITION BY subject), 2)      AS subject_avg,
       ROUND(G3 - AVG(G3) OVER (PARTITION BY subject), 2) AS gap_to_avg
FROM students
WHERE dropout_flag = 0
ORDER BY gap_to_avg ASC
LIMIT 8;

-- name: Q11 At-risk records by school and subject (uses view v_at_risk)
SELECT subject, school,
       COUNT(*)                AS at_risk_records,
       ROUND(AVG(absences),1)  AS avg_absences,
       ROUND(AVG(failures),2)  AS avg_past_failures
FROM v_at_risk
GROUP BY subject, school
ORDER BY at_risk_records DESC;

-- name: Q12 Maths vs Portuguese for students matched one-to-one on 13 background attributes (approximate, no student id exists)
WITH keyed AS (
    SELECT *,
           COUNT(*) OVER (PARTITION BY subject, school, sex, age, address, famsize, Pstatus,
                                       Medu, Fedu, Mjob, Fjob, reason, nursery, internet) AS key_count
    FROM students
),
m AS (SELECT * FROM keyed WHERE subject = 'Maths'      AND key_count = 1),
p AS (SELECT * FROM keyed WHERE subject = 'Portuguese' AND key_count = 1)
SELECT COUNT(*) AS matched_pairs,
       SUM(CASE WHEN p.pass_flag = 1 AND m.pass_flag = 0 THEN 1 ELSE 0 END) AS pass_por_fail_maths,
       SUM(CASE WHEN p.pass_flag = 0 AND m.pass_flag = 1 THEN 1 ELSE 0 END) AS pass_maths_fail_por,
       ROUND(AVG(m.G3),2) AS avg_maths_g3,
       ROUND(AVG(p.G3),2) AS avg_por_g3
FROM m JOIN p
  ON  m.school=p.school AND m.sex=p.sex AND m.age=p.age AND m.address=p.address
  AND m.famsize=p.famsize AND m.Pstatus=p.Pstatus AND m.Medu=p.Medu AND m.Fedu=p.Fedu
  AND m.Mjob=p.Mjob AND m.Fjob=p.Fjob AND m.reason=p.reason
  AND m.nursery=p.nursery AND m.internet=p.internet;
