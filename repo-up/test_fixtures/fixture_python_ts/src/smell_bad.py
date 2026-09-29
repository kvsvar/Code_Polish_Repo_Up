# smell_bad.py — intentional code smell fixture for Python smell rules
# This file is intentionally bad for testing purposes.

# Too-few-public-methods: class with only 1 public method
class TinyClass:
    def only_method(self):
        return 42


# Inconsistent return: function sometimes returns value, sometimes bare return
def inconsistent_fetch(data):
    if data is None:
        return  # bare return — no value
    if data == "error":
        return None  # explicit None — treated as bare
    result = process(data)  # undefined name: process
    return result  # valued return


# Long line (over 100 chars)
def long_line_function():
    some_very_long_variable_name_that_makes_this_line_exceed_one_hundred_characters_for_sure = "value_of_the_long_variable"


# Unused variable
def unused_var_example():
    unused = "this is never referenced"
    working = "this is used"
    return working


# Duplicate code (structural clone of clone_b below)
def clone_a(x):
    result = x * 2
    result = result + 10
    result = result - 5
    return result


def clone_b(y):
    result = y * 2
    result = result + 10
    result = result - 5
    return result


# Clean function — no smells
def clean_function(value: int) -> int:
    """Computes the double of value."""
    return value * 2
