SELECT
    ROUND(AVG(S.LAT_N), 4) -- Round the calculated median to 4 decimal places.
FROM
    (
        SELECT
            LAT_N,
            -- Assign a row number to each LAT_N value after sorting.
            -- @row_num is a session variable that increments with each row.
            @row_num:=@row_num + 1 AS rn
        FROM
            STATION,
            -- Initialize the session variable @row_num to 0.
            (SELECT @row_num:=0) AS init_var
        ORDER BY
            LAT_N -- Sort the latitudes in ascending order to find the median.
    ) AS S
WHERE
    
    S.rn IN (FLOOR((@row_num / 2) + 0.5), CEIL((@row_num / 2) + 0.5));
