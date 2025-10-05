import requests
import json
import time
import datetime as dt

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/events"

def parse_ts(ts_str):
  if not ts_str:
    return None
  for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ"):
    try:
      return dt.datetime.strptime(ts_str, fmt).replace(tzinfo=dt.timezone.utc)
    except ValueError:
      continue
  return None

def is_live_game_market(market, now_utc, max_hours_until_exp=4, min_hours_since_open=0.5):
  """
  Check if a market represents a currently live game (in progress).
  
  A game is "live" if:
  - Market is active/open and has no result
  - Game has already started (at least min_hours_since_open hours ago)
  - Game will expire soon (within max_hours_until_exp hours)
  """
  status = (market.get("status") or "").lower()
  result = market.get("result")

  # Must be active and not yet resolved
  if status not in ("open", "active") or (result and result != ""):
    return False

  open_time = parse_ts(market.get("open_time"))
  exp = (
    parse_ts(market.get("expected_expiration_time")) or
    parse_ts(market.get("latest_expiration_time")) or
    parse_ts(market.get("expiration_time"))
  )

  if not open_time or not exp:
    return False

  # Calculate hours since open and hours until expiration
  hours_since_open = (now_utc - open_time).total_seconds() / 3600
  hours_until_exp = (exp - now_utc).total_seconds() / 3600
  
  # Live games: started at least min_hours_since_open ago and expire within max_hours_until_exp
  return hours_since_open >= min_hours_since_open and 0 <= hours_until_exp <= max_hours_until_exp

def fetch_live_sports_events():
  """Fetch all currently live sports events (games in progress) from Kalshi API."""
  session = requests.Session()
  now_ts = int(time.time())
  now_utc = dt.datetime.now(dt.timezone.utc)
  
  params = {
    "status": "open",
    "limit": 200,
    "with_nested_markets": True,
    "min_close_ts": now_ts,
  }

  sports_events = []

  while True:
    response = session.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    events = data.get("events", [])
    
    for event in events:
      # Only include Sports events
      if event.get("category") != "Sports":
        continue
      
      # Check if event has any live game markets
      markets = event.get("markets", [])
      has_live_market = any(is_live_game_market(m, now_utc) for m in markets)
      
      if has_live_market:
        sports_events.append(event)

    cursor = data.get("cursor")
    if not cursor:
      break
    params["cursor"] = cursor

  return sports_events

if __name__ == "__main__":
  events = fetch_live_sports_events()
  print(json.dumps({"count": len(events), "events": events}, indent=2))
