if __name__ == '__main__':
    try:
        a_str = input()
        b_str = input()
        a = int(a_str)
        b = int(b_str)

        if 1 <= a <= 10**10 and 1 <= b <= 10**10:
            sum_result = a + b
            difference_result = a - b
            product_result = a * b

            print(sum_result)
            print(difference_result)
            print(product_result)
        else:
            print("Input values are outside the allowed range.")
    except ValueError:
        print("Invalid input. Please enter integers.")
