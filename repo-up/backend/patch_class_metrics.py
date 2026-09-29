"""Patch script: replace raw-dict metric findings in class_metrics.py with Finding objects."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'backend/analysis/metrics/class_metrics.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_marker = '    findings: list[dict] = []\n    for c in all_classes:'
new_block = '''    findings: list[dict] = []
    _wmc_spec  = get_rule("METRIC-HIGH-WMC")
    _dit_spec  = get_rule("METRIC-DEEP-DIT")
    _lcom_spec = get_rule("METRIC-LOW-COHESION")
    for c in all_classes:
        if c["public_methods"] > 15:
            findings.append(
                Finding(
                    rule_id="METRIC-HIGH-WMC",
                    category="Metrics",
                    title="High WMC -- many public methods",
                    description=(
                        f"\\'{c[\\'name\\']}\\' has {c[\\'public_methods\\']} public methods "
                        f"(WMC proxy). A high count suggests the class has too many "
                        f"responsibilities and may benefit from decomposition."
                    ),
                    severity="High",
                    rule=_wmc_spec.name if _wmc_spec else "High WMC",
                    resolution=_wmc_spec.resolution if _wmc_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )
        if c["dit"] >= 3:
            findings.append(
                Finding(
                    rule_id="METRIC-DEEP-DIT",
                    category="Metrics",
                    title="Deep Inheritance (DIT >= 3)",
                    description=(
                        f"\\'{c[\\'name\\']}\\' has an inheritance depth of {c[\\'dit\\']}. "
                        f"Deep chains can make behaviour harder to trace and test."
                    ),
                    severity="Medium",
                    rule=_dit_spec.name if _dit_spec else "Deep DIT",
                    resolution=_dit_spec.resolution if _dit_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )
        if c["lcom"] > 10:
            findings.append(
                Finding(
                    rule_id="METRIC-LOW-COHESION",
                    category="Metrics",
                    title="Low Cohesion (LCOM proxy > 10)",
                    description=(
                        f"\\'{c[\\'name\\']}\\' has a LCOM proxy value of {c[\\'lcom\\']} "
                        f"(methods - 1). A high value suggests the class may be "
                        f"doing too many unrelated things."
                    ),
                    severity="Medium",
                    rule=_lcom_spec.name if _lcom_spec else "Low Cohesion",
                    resolution=_lcom_spec.resolution if _lcom_spec else None,
                    file=c["filepath"],
                    line=c.get("line"),
                ).to_dict()
            )'''

# Find the start of the old findings block
idx = content.find(old_marker)
if idx == -1:
    print("FAIL: marker not found")
    sys.exit(1)

# Find where the old findings block ends (at: "    if not all_classes:")
end_marker = '\n\n    if not all_classes:'
end_idx = content.find(end_marker, idx)
if end_idx == -1:
    print("FAIL: end marker not found")
    sys.exit(1)

content = content[:idx] + new_block + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: class_metrics.py patched successfully")
