def average(array):

    sum_of_unique = sum(unique_elements)

    # Calculate the number of unique elements.
    count_of_unique = len(unique_elements)

    
    if count_of_unique == 0:
        return 0.0  # Or handle as per problem's specific requirements for empty set
    else:
        return sum_of_unique / count_of_unique

if __name__ == '__main__':
    n = int(input())
    arr = list(map(int, input().split()))
    result = average(arr)
    print(result)