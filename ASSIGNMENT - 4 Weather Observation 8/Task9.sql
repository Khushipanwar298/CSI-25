SELECT
    H.hacker_id,      -- Select the hacker's ID
    H.name,           -- Select the hacker's name
    SUM(S.max_score) AS total_score -- Calculate the sum of maximum scores for each hacker
FROM
    Hackers AS H      -- Alias the Hackers table as H
JOIN (
    -- Subquery to get the maximum score for each hacker on each challenge
    SELECT
        S.hacker_id,
        S.challenge_id,
        MAX(S.score) AS max_score
    FROM
        Submissions AS S -- Alias the Submissions table as S
    GROUP BY
        S.hacker_id,     -- Group by hacker and challenge to find the max score for that specific attempt
        S.challenge_id
) AS S ON H.hacker_id = S.hacker_id -- Join the hackers with their max scores per challenge
GROUP BY
    H.hacker_id,      -- Group by hacker again to sum up their max scores across all challenges
    H.name
HAVING
    total_score > 0   -- Filter out hackers who have a total score of 0
ORDER BY
    total_score DESC, -- Order the leaderboard by total score in descending order
    H.hacker_id ASC;  -- If total scores are tied, order by hacker ID in ascending order
                                        
