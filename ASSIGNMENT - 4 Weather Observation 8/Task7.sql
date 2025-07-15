

SELECT
    H.hacker_id, -- Select the hacker's ID
    H.name       -- Select the hacker's name
FROM
    Hackers H    -- Alias the Hackers table as H
JOIN
    Submissions S ON H.hacker_id = S.hacker_id -- Join Hackers with Submissions on hacker_id
JOIN
    Challenges C ON S.challenge_id = C.challenge_id -- Join Submissions with Challenges on challenge_id
JOIN
    Difficulty D ON C.difficulty_level = D.difficulty_level -- Join Challenges with Difficulty on difficulty_level
WHERE
    S.score = D.score -- Filter for submissions where the submitted score matches the full score for that difficulty level
GROUP BY
    H.hacker_id, -- Group the results by hacker_id
    H.name       -- And by hacker's name to count full scores per hacker
HAVING
    COUNT(S.challenge_id) > 1 -- Filter groups to include only hackers with more than one full score
ORDER BY
    COUNT(S.challenge_id) DESC, -- Order primarily by the count of full score challenges in descending order
    H.hacker_id ASC;            -- Secondarily order by hacker_id in ascending order for ties
