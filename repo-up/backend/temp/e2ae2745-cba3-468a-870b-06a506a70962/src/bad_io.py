import requests
def fetch():
    r = requests.get('http://test.com')
    return r.text
