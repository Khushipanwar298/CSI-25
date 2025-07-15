def compress_string(s):
    if not s:
        return ""  # Handle empty string case

    result = []
    count = 1
    prev_char = s[0]  # Store the first character

    for i in range(1, len(s)):
        if s[i] == prev_char:
            count += 1
        else:
            result.append(f"({count}, {prev_char})")
            prev_char = s[i]
            count = 1

    # Add the last group of characters
    result.append(f"({count}, {prev_char})")
    return ' '.join(result)

if __name__ == "__main__":
    input_string = input()
    compressed_result = compress_string(input_string)
    print(compressed_result)