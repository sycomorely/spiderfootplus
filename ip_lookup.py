import sys
import requests
import json

if len(sys.argv) < 2:
    print("Usage: python ip_lookup.py <ip_address>")
    sys.exit(1)

ip = sys.argv[1]
url = f"http://ip-api.com/json/{ip}?fields=66846719"

response = requests.get(url)
if response.status_code == 200:
    print("IP Lookup Result:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.status_code}")
