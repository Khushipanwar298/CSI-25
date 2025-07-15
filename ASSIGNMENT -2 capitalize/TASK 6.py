import collections

# Read X, the number of shoes (not directly used in logic, but part of input format)
X = int(input())

# Read the space-separated list of shoe sizes and create a Counter object
# collections.Counter is a dictionary subclass for counting hashable objects.
# It stores elements as dictionary keys and their counts as dictionary values.
shoe_sizes = list(map(int, input().split()))
shoe_inventory = collections.Counter(shoe_sizes)

# Read N, the number of customers
N = int(input())

# Initialize total earnings
total_earnings = 0

# Iterate through each customer
for _ in range(N):
    # Read the desired shoe size (s) and price (p) for the current customer
    size, price = map(int, input().split())

    # Check if the desired shoe size is available in the inventory
    # If shoe_inventory[size] > 0, it means there's at least one shoe of that size.
    if shoe_inventory[size] > 0:
        # If available, "sell" the shoe by decrementing its count in the inventory
        shoe_inventory[size] -= 1
        # Add the price to the total earnings
        total_earnings += price

# Print the final total earnings
print(total_earnings)
