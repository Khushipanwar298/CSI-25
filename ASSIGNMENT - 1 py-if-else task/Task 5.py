def is_leap(year):
    leap = False
    if (year % 4 == 0):  # Check if divisible by 4
        if (year % 100 == 0):  # If divisible by 100, check divisibility by 400
            if (year % 400 == 0):
                leap = True  # Divisible by 400, it's a leap year
            else:
                leap = False # Divisible by 100, not by 400, not a leap year
        else:
            leap = True  # Divisible by 4, not by 100, it's a leap year
    else:
        leap = False # Not divisible by 4, not a leap year

    return leap

year = int(input())
print(is_leap(year))