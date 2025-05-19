def calculate_probability(N, letters, K):
    count_a = letters.count('a')  # Count occurrences of 'a'
    total_combinations = 1
    selected_combinations_without_a = 1

    # Calculate the total number of combinations (N choose K)
    for i in range(K):
        total_combinations *= (N - i)
    for i in range(1, K + 1):
        total_combinations //= i

    if count_a == 0:
        return 0.000

    # Calculate combinations without 'a'
    without_a_count = N - count_a
    if without_a_count >= K:
        for i in range(K):
            selected_combinations_without_a *= (without_a_count - i)
        for i in range(1, K + 1):
            selected_combinations_without_a //= i
        probability_without_a = selected_combinations_without_a / total_combinations
        probability_with_a = 1 - probability_without_a
    else:
        probability_with_a = 1.000

    return round(probability_with_a, 3)

if __name__ == "__main__":
    N = int(input())
    letters = input().split()
    K = int(input())

    result = calculate_probability(N, letters, K)
    print(result)
