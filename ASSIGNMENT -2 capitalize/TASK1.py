
import math
import os
import random
import re
import sys

# Complete the solve function below.
def solve(s):

    words = s.split(' ') # Split the string by spaces
    capitalized_words = []

    for word in words:
        if word: # Check if the word is not empty
            if word[0].isalpha(): # Check if the first character is an alphabet
                capitalized_words.append(word[0].upper() + word[1:])
            else:
                capitalized_words.append(word) # If not an alphabet, keep the word as is
        else:
            capitalized_words.append("") # Append an empty string for multiple spaces

    return ' '.join(capitalized_words)
if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    s = input()

    result = solve(s)

    fptr.write(result + '\n')

    fptr.close()
