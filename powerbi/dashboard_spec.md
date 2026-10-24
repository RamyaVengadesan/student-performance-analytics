# Power BI build guide

This guide documents how to build the Power BI report from the prepared dataset, DAX measures and theme. The prepared CSV, measures and theme are included; the report pages still need to be assembled in Power BI Desktop, and the DAX has not yet been tested there.

## 1. Load the data
1. Power BI Desktop > Get data > Text/CSV > `powerbi_students.csv` > Load.
2. Rename the table to `Students`.
3. Check types: grades, absences and ids as Whole number; `risk_of_failing` as Decimal (format as %).
4. Import `theme.json` (View > Themes > Browse for themes).
5. Add the measures from `measures.dax` into a `_Measures` table, and add the sort column for `absence_band`.

## 2. Page 1: Overview
- Cards: Total Records, Pass Rate, Avg Final Grade, Avg Absences, High Risk Records, Possible Dropouts.
- Clustered column: `Subject` by `Pass Rate` and `Avg Final Grade`.
- Histogram-style column chart: `G3` (as a category) by `Total Records`, with a constant line at 10.
- Slicers: `subject`, `school`, `sex`, `address`.

## 3. Page 2: Attendance and effort
- Column chart: `absence_band` (sorted by Absence Band Order) by `Active Pass Rate`.
- Scatter: X = `absences`, Y = `G3`, filtered to `dropout_flag` = 0, with a trend line (Analytics pane).
- Column chart: `studytime` by `Active Avg Final Grade`; add `Avg Grade Change` as a second visual.
- Add a text box: "G3 = 0 records excluded: no attendance data".

## 4. Page 3: Background factors
- Column chart: `failures` by `Pass Rate`.
- Column chart: `higher_label` by `Pass Rate`.
- Matrix: rows = `address`, columns = `internet`, values = `Active Avg Final Grade` (urban students show the internet gap, rural do not).
- Column chart: `avg_parent_edu` bucketed (Data groups, size 1) by `Pass Rate`.

## 5. Page 4: Early-warning list
- Column chart: `risk_level` by `Actual Fail Rate` (shows the model separates risk levels).
- Table: `student_id`, `subject`, `school`, `G1`, `absences`, `failures`, `risk_of_failing`; filter `risk_level` = High; sort by `risk_of_failing` descending; add conditional formatting on `risk_of_failing`.
- Note: this table is for planning support. Treat scores as a prompt for a conversation, not a label on a student.

## 6. Finishing
- Turn on cross-filtering between visuals, set consistent titles, and align to a grid.
- Add a page footer with the source: Cortez and Silva (2008), UCI Student Performance, CC BY 4.0.
- Save as `Student_Performance_Dashboard.pbix`, export a PDF, and add screenshots to the GitHub README.
