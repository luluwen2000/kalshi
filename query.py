import requests

url = "https://api.elections.kalshi.com/trade-api/v2/events"

response = requests.get(url)

print(response.json())