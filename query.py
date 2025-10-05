import requests
import json

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/events"

def fetch_live_sports_events():
  session = requests.Session()
  params = {
    "status": "open",
    "limit": 200,
    # "with_nested_markets": False,  # uncomment if you want to exclude nested markets
  }

  sports_events = []

  while True:
    response = session.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    for event in data.get("events", []):
      if event.get("category") == "Sports":
        sports_events.append(event)

    cursor = data.get("cursor")
    if not cursor:
      break
    params["cursor"] = cursor

  return sports_events

if __name__ == "__main__":
  events = fetch_live_sports_events()
  print(json.dumps({"count": len(events), "events": events}, indent=2))