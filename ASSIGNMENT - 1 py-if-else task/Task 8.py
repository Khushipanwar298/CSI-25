if __name__ == '__main__':
    n = int(input())
    integer_list = list(map(int, input().split()))  # Convert map object to a list
    
    # Check if the input list is empty
    if not integer_list:
        print(hash(tuple()))  # Print hash of an empty tuple if input is empty
    else:
        # Create a tuple from the integer list
        t = tuple(integer_list)
        
        # Compute and print the hash of the tuple
        print(hash(t))
