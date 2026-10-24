-- Schema for the student performance database (SQLite).
-- One row = one student-subject record (Maths or Portuguese). There is no student id, so a person
-- who appears in both subject files has two rows.
-- MySQL notes: replace INTEGER PRIMARY KEY with INT PRIMARY KEY (or AUTO_INCREMENT),
-- and TEXT with VARCHAR(n) for indexed columns.

DROP VIEW IF EXISTS v_at_risk;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    student_id        INTEGER PRIMARY KEY,
    school            TEXT NOT NULL CHECK (school IN ('GP','MS')),
    sex               TEXT NOT NULL CHECK (sex IN ('F','M')),
    age               INTEGER NOT NULL,
    address           TEXT,
    famsize           TEXT,
    Pstatus           TEXT,
    Medu              INTEGER,
    Fedu              INTEGER,
    Mjob              TEXT,
    Fjob              TEXT,
    reason            TEXT,
    guardian          TEXT,
    traveltime        INTEGER,
    studytime         INTEGER,
    failures          INTEGER,
    schoolsup         INTEGER,
    famsup            INTEGER,
    paid              INTEGER,
    activities        INTEGER,
    nursery           INTEGER,
    higher            INTEGER,
    internet          INTEGER,
    romantic          INTEGER,
    famrel            INTEGER,
    freetime          INTEGER,
    goout             INTEGER,
    Dalc              INTEGER,
    Walc              INTEGER,
    health            INTEGER,
    absences          INTEGER NOT NULL CHECK (absences >= 0),
    G1                INTEGER CHECK (G1 BETWEEN 0 AND 20),
    G2                INTEGER CHECK (G2 BETWEEN 0 AND 20),
    G3                INTEGER CHECK (G3 BETWEEN 0 AND 20),
    subject           TEXT NOT NULL CHECK (subject IN ('Maths','Portuguese')),
    dropout_flag      INTEGER,
    high_absence_flag INTEGER,
    pass_flag         INTEGER,
    grade_band        TEXT,
    absence_band      TEXT,
    grade_change      INTEGER,
    avg_parent_edu    REAL,
    alc_total         INTEGER
);

CREATE INDEX idx_students_subject ON students(subject);
CREATE INDEX idx_students_school  ON students(school);

-- Students who may need early support: second-period grade below the pass mark,
-- or borderline grade combined with heavy absences. Dropout records are excluded.
CREATE VIEW v_at_risk AS
SELECT student_id, subject, school, G1, G2, absences, failures
FROM students
WHERE dropout_flag = 0
  AND (G2 < 10 OR (G2 BETWEEN 10 AND 11 AND absences >= 10));
