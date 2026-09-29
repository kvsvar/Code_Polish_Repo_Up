"""
Source: Ferreira, K.A.M., Bigonha, M.A.S., Bigonha, R.S., Mendes, L.F.O.,
Almeida, H.C. (2012). "Identifying thresholds for object-oriented
software metrics." Journal of Systems and Software 85(2), 244-257.
Table 3 — General thresholds for OO software metrics.
Derived from 40 open-source Java systems, 26,000+ classes.
"""

THRESHOLDS = {
    "cof":                 {"good": 0.02, "regular_upper": 0.14},
    "afferent_couplings":  {"good": 1,    "regular_upper": 20},
    "public_fields":       {"good": 0,    "regular_upper": 10},
    "public_methods":      {"good_upper": 10, "regular_upper": 40},
    "dit":                 {"typical": 2},
    "lcom":                {"good": 0,    "regular_upper": 20},
}

def rate_metric(name: str, value: float) -> str:
    """Returns 'good' | 'regular' | 'bad'."""
    t = THRESHOLDS[name]

    if name == "dit":
        if value <= t["typical"]:
            return "good"
        elif value <= t["typical"] + 1:
            return "regular"
        return "bad"

    if name == "public_methods":
        if value <= t["good_upper"]:
            return "good"
        if value <= t["regular_upper"]:
            return "regular"
        return "bad"

    if value <= t["good"]:
        return "good"
    if value <= t["regular_upper"]:
        return "regular"
    return "bad"
