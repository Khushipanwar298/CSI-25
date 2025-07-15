SELECT
    W.id,          -- Select the wand's ID
    WP.age,        -- Select the wand's age
    W.coins_needed, -- Select the coins needed for the wand
    W.power        -- Select the wand's power
FROM
    Wands AS W     -- Alias the Wands table as W
JOIN
    Wands_Property AS WP ON W.code = WP.code -- Join Wands with Wands_Property on their common 'code'
WHERE
    WP.is_evil = 0 -- Filter for non-evil wands (is_evil = 0)
    AND W.coins_needed = (
        -- Subquery to find the minimum coins_needed for each unique combination of power and age
        SELECT
            MIN(W2.coins_needed)
        FROM
            Wands AS W2
        JOIN
            Wands_Property AS WP2 ON W2.code = WP2.code
        WHERE
            WP2.is_evil = 0     -- Ensure the subquery also considers only non-evil wands
            AND W2.power = W.power -- Match power with the outer query's wand power
            AND WP2.age = WP.age   -- Match age with the outer query's wand age
    )
ORDER BY
    W.power DESC, -- Primary sorting: Order by power in descending order
    WP.age DESC;  -- Secondary sorting: If powers are same, order by age in descending order