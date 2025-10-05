import requests
import json

url = "https://api.elections.kalshi.com/trade-api/v2/events"

response = requests.get(url)

print(json.dumps(response.json(), indent=2))