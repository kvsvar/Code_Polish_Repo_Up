# Python cross-language fixture — smell.py
# Conceptually equivalent smells: too-few-methods, long line, unused var, inconsistent return.

class ThinService:
    def only_one(self):
        return "only one public method — too few"


def fetch_with_inconsistent_return(value):
    if value is None:
        return
    processed = str(value)
    return processed


def has_unused_variable():
    unused_data = "this variable is never used after assignment"
    result = "this is returned"
    return result


# Long line (>100 chars) — intentional smell
VERY_LONG_CONFIG_STRING = "this_is_a_very_long_string_that_exists_purely_to_exceed_the_one_hundred_character_line_limit_threshold"
