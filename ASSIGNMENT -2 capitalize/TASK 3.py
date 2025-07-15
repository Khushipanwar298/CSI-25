import textwrap


def wrap(string, max_width):
    """
    Wraps the input string into a paragraph of a given width.

    Args:
        string (str): The long string to be wrapped.
        max_width (int): The maximum width of each line in the wrapped paragraph.

    Returns:
        str: A single string with newline characters ('\n') where the breaks should be.
    """
    # Use textwrap.fill to wrap the string.
    # textwrap.fill automatically handles breaking lines and inserting newlines.
    wrapped_string = textwrap.fill(string, max_width)
    return wrapped_string

if __name__ == '__main__':
    string, max_width = input(), int(input())
    result = wrap(string, max_width)
    print(result)