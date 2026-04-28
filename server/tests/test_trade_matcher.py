import os

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_matcher import build_want_graph, find_cycles, find_trade_loops


def test_build_want_graph():
    listings = [
        {
            "user_id": "alice",
            "item_label": "paint set",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["brushes"],
        },
        {
            "user_id": "bob",
            "item_label": "brushes",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["paint set"],
        },
    ]
    graph = build_want_graph(listings)
    assert "alice" in graph
    assert "bob" in graph
    assert len(graph["alice"]) >= 1
    assert graph["alice"][0]["user_id"] == "bob"


def test_find_two_party_cycle():
    listings = [
        {
            "user_id": "alice",
            "item_label": "paint set",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["brushes"],
        },
        {
            "user_id": "bob",
            "item_label": "brushes",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["paint set"],
        },
    ]
    graph = build_want_graph(listings)
    cycles = find_cycles(graph, max_length=4)
    assert len(cycles) >= 1
    assert len(cycles[0]) == 2


def test_find_three_party_cycle():
    listings = [
        {
            "user_id": "alice",
            "item_label": "paint set",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["brushes"],
        },
        {
            "user_id": "bob",
            "item_label": "brushes",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["canvas"],
        },
        {
            "user_id": "charlie",
            "item_label": "canvas",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["paint set"],
        },
    ]
    graph = build_want_graph(listings)
    cycles = find_cycles(graph, max_length=4)
    assert len(cycles) >= 1
    # Should find the 3-party cycle
    three_party = [c for c in cycles if len(c) == 3]
    assert len(three_party) >= 1


def test_find_trade_loops_api():
    listings = [
        {
            "id": "l1",
            "user_id": "alice",
            "item_label": "paint set",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["brushes"],
        },
        {
            "id": "l2",
            "user_id": "bob",
            "item_label": "brushes",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["paint set"],
        },
    ]
    results = find_trade_loops(listings, max_length=4)
    assert len(results) >= 1
    assert results[0]["cycle_length"] == 2
    assert "alice" in results[0]["participants"]
    assert "bob" in results[0]["participants"]
    assert "score" in results[0]
    assert "description" in results[0]


def test_no_cycles_when_no_matches():
    listings = [
        {
            "user_id": "alice",
            "item_label": "paint set",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["bicycle"],
        },
        {
            "user_id": "bob",
            "item_label": "brushes",
            "trade_value_credits": 30.0,
            "tags": ["art"],
            "wants_in_return": ["laptop"],
        },
    ]
    graph = build_want_graph(listings)
    cycles = find_cycles(graph, max_length=4)
    assert len(cycles) == 0
