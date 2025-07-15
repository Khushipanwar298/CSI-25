SELECT DISTINCT CITY
FROM STATION
WHERE
    -- Check if the first character of CITY is a vowel (case-insensitive)
    LOWER(SUBSTRING(CITY, 1, 1)) IN ('a', 'e', 'i', 'o', 'u')
    AND
    -- Check if the last character of CITY is a vowel (case-insensitive)
    LOWER(SUBSTRING(CITY, LENGTH(CITY), 1)) IN ('a', 'e', 'i', 'o', 'u');