
SELECT
    -- Round the final Euclidean distance to 4 decimal places.
    ROUND(
        SQRT(
            -- Calculate (max(LAT_N) - min(LAT_N))^2
            POWER(MAX(LAT_N) - MIN(LAT_N), 2)
            +
            -- Calculate (max(LONG_W) - min(LONG_W))^2
            POWER(MAX(LONG_W) - MIN(LONG_W), 2)
        ),
    4)
FROM
    STATION;
