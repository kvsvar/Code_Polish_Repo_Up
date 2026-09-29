"""
thresholds.py — empirical metric thresholds for good/regular/bad classification.

Primary source
--------------
Ferreira, K.A.M., Bigonha, M.A.S., Bigonha, R.S., Mendes, L.F.O.,
Almeida, H.C. (2012).  "Identifying thresholds for object-oriented
software metrics."  Journal of Systems and Software 85(2), 244-257.
Derived from 40 open-source Java systems, 26,000+ classes (Table 3).

Note on proxy metrics
----------------------
The metrics here are *proxies* adapted from the CK metric suite:
- ``public_methods``  — public method count used as WMC proxy
- ``lcom``            — (methods − 1) used as LCOM proxy
These are simplifications of the originals; the thresholds are adjusted
accordingly to remain meaningful under the proxy definition.

Threshold semantics
-------------------
``good``         → value ≤ this → rated "good"
``regular_upper`` → good < value ≤ this → rated "regular"
anything above   → rated "bad"

For ``public_methods`` (WMC proxy):
``good_upper``   → value ≤ this → rated "good"
``regular_upper`` → good_upper < value ≤ this → rated "regular"

For ``dit``:
``typical``      → value ≤ this → rated "good"
                   value ≤ typical + 1 → "regular"
                   otherwise → "bad"
"""

THRESHOLDS: dict[str, dict] = {
    "cof":                  {"good": 0.02,  "regular_upper": 0.14},
    "afferent_couplings":   {"good": 1,     "regular_upper": 20},
    "public_fields":        {"good": 0,     "regular_upper": 10},
    "public_methods":       {"good_upper": 10, "regular_upper": 40},  # WMC proxy
    "dit":                  {"typical": 2},
    "lcom":                 {"good": 0,     "regular_upper": 20},     # LCOM proxy
}


def rate_metric(name: str, value: float) -> str:
    """Return ``'good'`` | ``'regular'`` | ``'bad'`` for *value* of *name*.

    Handles all threshold shapes defined in THRESHOLDS.
    Falls back to ``'good'`` for unknown metric names.
    """
    if name not in THRESHOLDS:
        return "good"

    t = THRESHOLDS[name]

    if name == "dit":
        if value <= t["typical"]:
            return "good"
        if value <= t["typical"] + 1:
            return "regular"
        return "bad"

    if name == "public_methods":
        if value <= t["good_upper"]:
            return "good"
        if value <= t["regular_upper"]:
            return "regular"
        return "bad"

    # Standard upper-bound pattern
    if value <= t["good"]:
        return "good"
    if value <= t["regular_upper"]:
        return "regular"
    return "bad"
