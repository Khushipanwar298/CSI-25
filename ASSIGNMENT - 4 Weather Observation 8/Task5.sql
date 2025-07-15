-- This query generates a report containing student names, grades, and marks.
-- It handles specific conditions for students with grades below 8 and applies complex sorting rules.

SELECT
    -- Use a CASE statement to determine the student's name to display.
    -- If the grade is 8 or higher, show the student's actual name.
    -- If the grade is less than 8, display 'NULL' as the name.
    CASE
        WHEN G.Grade >= 8 THEN S.Name
        ELSE NULL
    END AS Name,
    -- Select the Grade from the Grades table.
    G.Grade,
    -- Select the Marks from the Students table.
    S.Marks
FROM
    -- Join the Students table (aliased as S) with the Grades table (aliased as G).
    Students S
JOIN
    Grades G ON S.Marks BETWEEN G.Min_Mark AND G.Max_Mark
ORDER BY
    -- Primary sorting: Order by Grade in descending order (higher grades first).
    G.Grade DESC,
    -- Secondary sorting for grades 8 and above: Order by Name alphabetically (ascending).
    -- The CASE statement ensures this ordering only applies to students with Grade >= 8.
    CASE
        WHEN G.Grade >= 8 THEN S.Name
        ELSE NULL
    END ASC,
    -- Tertiary sorting for grades below 8: Order by Marks in ascending order.
    -- The CASE statement ensures this ordering only applies to students with Grade < 8.
    -- When Grade >= 8, this part of the order by clause will be effectively ignored
    -- because the previous CASE (S.Name) would have already sorted them.
    -- If S.Name is NULL (for grades < 8), this becomes the relevant sort for those rows.
    CASE
        WHEN G.Grade < 8 THEN S.Marks
        ELSE NULL
    END ASC;