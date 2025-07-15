T = int(input())

# Iterate through each test case
for _ in range(T):
    try:
        # Read the space-separated values of a and b as strings
        a_str, b_str = input().split()

        # Attempt to convert a and b to integers
        a = int(a_str)
        b = int(b_str)

        # Perform integer division
        result = a // b
        print(result)
    except ZeroDivisionError:
        # Handle the ZeroDivisionError if b is 0
        print("Error Code: integer division or modulo by zero")
    except ValueError as e:
        # Handle the ValueError if a or b cannot be converted to an integer
        # The error message from the exception object 'e' contains the specific detail
        print(f"Error Code: {e}")
    except Exception as e:
        # Catch any other unexpected exceptions (good practice, though not strictly
        # required by this problem's specific error messages)
        print(f"An unexpected error occurred: {e}")