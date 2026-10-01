import requests
import json

r1 = requests.post('http://localhost:8000/analyze', files={'file': open('test_fixtures/fixture_sandbox.zip', 'rb')}, stream=True)
sess = ''
for l in r1.iter_lines():
    line = l.decode('utf-8')
    if 'session_id' in line:
        data = json.loads(line.replace('data: ', ''))
        sess = data['result']['session_id']
        break

print(f"Session: {sess}")
r2 = requests.post('http://localhost:8000/repair', json={
    'session_id': sess, 
    'finding': {
        'rule_id': 'SEC-CWE-502', 
        'language': 'Python', 
        'file': 'fixture_sandbox/main.py', 
        'line': 6, 
        'category': 'Security', 
        'title': 'Unsafe Deserialization', 
        'description': 'desc', 
        'severity': 'High'
    }
})
print(r2.status_code)
print(r2.json())
