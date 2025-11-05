import requests
import json

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/events"


def fetch_event_by_ticker(event_ticker, with_nested_markets=False):
    """
    Fetch detailed event data by event ticker.
    
    Args:
        event_ticker: The event ticker to fetch
        with_nested_markets: If true, include markets within the event object
    
    Returns:
        Full event data from the API
    """
    url = f"{BASE_URL}/{event_ticker}"
    params = {}
    if with_nested_markets:
        params["with_nested_markets"] = "true"
    
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


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


def filter_events(event_stream, predicate):
    """
    Generic filter for event streams.
    Yields only events that match the given predicate function.
    
    Args:
        event_stream: An iterable/generator of events
        predicate: A function that takes an event and returns True/False
    """
    for event in event_stream:
        if predicate(event):
            yield event


def limit_events(event_stream, limit=None):
    """
    Limit the number of events from a stream.
    
    Args:
        event_stream: An iterable/generator of events
        limit: Maximum number of events to yield (None for unlimited)
    """
    if limit is None:
        yield from event_stream
    else:
        for i, event in enumerate(event_stream):
            if i >= limit:
                break
            yield event


def enrich_events(event_stream, with_nested_markets=False):
    """
    Enrich events by fetching detailed data for each event ticker.
    
    Args:
        event_stream: An iterable/generator of events (with event_ticker field)
        with_nested_markets: If true, include markets within the event object
    
    Yields:
        Full event data from the /events/{event_ticker} endpoint
    """
    for event in event_stream:
        event_ticker = event.get("event_ticker")
        if event_ticker:
            detailed_event = fetch_event_by_ticker(event_ticker, with_nested_markets)
            yield detailed_event


def is_sports(event):
    """Predicate to check if an event is in the Sports category."""
    return event.get("category") == "Sports"


def stream_sports_events():
    """
    Generator that streams only Sports category events from Kalshi.
    Composed from stream_events() and filter_events().
    """
    return filter_events(stream_events(), is_sports)


if __name__ == "__main__":
    # Configure how many events to print (None for all)
    MAX_EVENTS = 10 
    
    # Compose: stream sports events -> enrich with detailed data -> limit
    events = limit_events(
        enrich_events(
            stream_sports_events(),
            with_nested_markets=True
        ),
        limit=MAX_EVENTS
    )
    
    for event in events:
        print(json.dumps(event, indent=2))
        print()  # blank line between events
