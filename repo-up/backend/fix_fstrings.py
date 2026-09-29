import sys
sys.stdout.reconfigure(encoding='utf-8')

path = 'backend/analysis/metrics/class_metrics.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the broken f-strings
content = content.replace(r"f\'\\'{c[\'name\']}\\' has {c[\'public_methods\']} public methods '", "f\"'{c['name']}' has {c['public_methods']} public methods \"")
content = content.replace(r"f'\\'{c[\'name\']}\\' has {c[\'public_methods\']} public methods '", "f\"'{c['name']}' has {c['public_methods']} public methods \"")
content = content.replace(r"f\"\\'{c[\'name\']}\\' has {c[\'public_methods\']} public methods \"", "f\"'{c['name']}' has {c['public_methods']} public methods \"")

content = content.replace(r"f\"\\'{c[\'name\']}\\' has an inheritance depth of {c[\'dit\']}. \"", "f\"'{c['name']}' has an inheritance depth of {c['dit']}. \"")

content = content.replace(r"f\"\\'{c[\'name\']}\\' has a LCOM proxy value of {c[\'lcom\']} \"", "f\"'{c['name']}' has a LCOM proxy value of {c['lcom']} \"")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: fixed f-strings')
