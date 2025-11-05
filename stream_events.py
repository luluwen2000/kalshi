import requests

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/events"


def fetch_page(cursor=None):
    """Fetch one page from Kalshi /events."""
    params = {}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def stream_events():
    """
    Generator that keeps pulling pages and yielding individual events.
    Stops when the API stops giving a cursor.
    """
    cursor = None
    while True:
        data = fetch_page(cursor)
        events = data.get("events", [])
        for ev in events:
            yield ev

        cursor = data.get("cursor")
        if not cursor:
            break  # no more pages


if __name__ == "__main__":
    # simple demo: print them all
    for event in stream_events():
        print(event)
