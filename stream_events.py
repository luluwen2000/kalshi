import requests
import json

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2/events"


# ============================================================================
# FETCH FUNCTIONS - Get data from URLs
# ============================================================================

def fetch_from_events_list(cursor=None):
    """
    FETCH from URL_A: /events endpoint (paginated list of all events).
    
    Returns:
        Response JSON with events array and cursor
    """
    params = {}
    if cursor:
        params["cursor"] = cursor
    resp = requests.get(BASE_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_from_event_detail(event_ticker, with_nested_markets=False):
    """
    FETCH from URL_B: /events/{event_ticker} endpoint (detailed event data).
    
    Args:
        event_ticker: The event ticker to fetch
        with_nested_markets: If true, include markets within the event object
    
    Returns:
        Response JSON with detailed event data
    """
    url = f"{BASE_URL}/{event_ticker}"
    params = {}
    if with_nested_markets:
        params["with_nested_markets"] = "true"
    
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


# ============================================================================
# STREAM FUNCTIONS - Transform fetched data into streams
# ============================================================================

def stream_from_events_list():
    """
    Stream events from paginated /events endpoint.
    Handles pagination automatically, yielding events one by one.
    """
    cursor = None
    while True:
        data = fetch_from_events_list(cursor)
        events = data.get("events", [])
        for event in events:
            yield event

        cursor = data.get("cursor")
        if not cursor:
            break


# ============================================================================
# TRANSFORMATION STEPS - Process stream data
# ============================================================================

def filter(stream, predicate):
    """
    Filter stream by predicate.
    
    Args:
        stream: Input stream/iterable
        predicate: Function that returns True/False for each item
    """
    for item in stream:
        if predicate(item):
            yield item


def limit(stream, limit=None):
    """
    Limit number of items in stream.
    
    Args:
        stream: Input stream/iterable
        limit: Maximum items to yield (None for unlimited)
    """
    if limit is None:
        yield from stream
    else:
        for i, item in enumerate(stream):
            if i >= limit:
                break
            yield item


def enrich_with_details(stream, with_nested_markets=False):
    """
    Enrich each event by fetching from detail endpoint (URL_B).
    
    Takes event tickers from stream and fetches full details.
    
    Args:
        stream: Stream of events with event_ticker field
        with_nested_markets: Include markets in response
    """
    for event in stream:
        event_ticker = event.get("event_ticker")
        if event_ticker:
            detailed_data = fetch_from_event_detail(event_ticker, with_nested_markets)
            yield detailed_data


def map(stream, transform_fn):
    """
    Map/transform each item in stream.
    
    Args:
        stream: Input stream/iterable
        transform_fn: Function to transform each item
    """
    for item in stream:
        yield transform_fn(item)


def extract_markets(stream):
    """
    Extract markets from event stream.
    Flattens the stream so each market becomes a separate item.
    Preserves event-level data (like category) by adding it to each market.
    
    Args:
        stream: Stream of events with markets field
    
    Yields:
        Individual market objects enriched with event data
    """
    for item in stream:
        # Handle both nested and top-level markets
        event_data = item.get("event", item)
        markets = event_data.get("markets", [])
        event_category = event_data.get("category")
        
        for market in markets:
            # Enrich market with event-level data
            enriched_market = dict(market)
            enriched_market["event_category"] = event_category
            yield enriched_market


def to_market_summary(stream):
    """
    Transform market objects to simplified summary containers.
    
    Args:
        stream: Stream of market objects
    
    Yields:
        Dicts with only the fields we care about
    """
    for market in stream:
        yield {
            "event_ticker": market.get("event_ticker"),
            "category": market.get("event_category"),
            "last_price": market.get("last_price"),
            "title": market.get("title")
        }


def is_sports_event(event):
    """Check if event is in Sports category."""
    return event.get("category") == "Sports"


if __name__ == "__main__":
    # Configure how many events to print (None for all)
    # MAX_EVENTS = 100
    MAX_EVENTS = 1
    
    stream = stream_from_events_list()
    stream = filter(stream, is_sports_event)
    stream = limit(stream, limit=MAX_EVENTS)
    stream = enrich_with_details(stream, with_nested_markets=True)
    stream = extract_markets(stream)
    stream = to_market_summary(stream)
    
    for market in stream:
        print(json.dumps(market, indent=2))
        print()
