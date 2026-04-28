import os
import tempfile

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_service import TradeService


def test_propose_trade_with_exact_match():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    alice_listing = svc.create_listing(
        user_id="alice",
        item_label="acrylic paint set",
        description="24 colors",
        condition="good",
        valuation_median_usd=40.0,
        trade_value_credits=40.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )

    bob_listing = svc.create_listing(
        user_id="bob",
        item_label="paint brushes",
        description="assorted sizes",
        condition="good",
        valuation_median_usd=40.0,
        trade_value_credits=40.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )

    match = svc.propose_trade(
        listing_id=alice_listing["id"],
        requester_id="bob",
        offered_listing_id=bob_listing["id"],
    )
    assert match["status"] == "pending"
    assert match["owner_id"] == "alice"

    result = svc.accept_trade(match["id"], user_id="alice")
    assert result["status"] == "completed"


def test_propose_trade_with_credit_top_up():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    alice_listing = svc.create_listing(
        user_id="alice",
        item_label="canvas set",
        description="5 stretched canvases",
        condition="good",
        valuation_median_usd=50.0,
        trade_value_credits=50.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )

    bob_listing = svc.create_listing(
        user_id="bob",
        item_label="palette knives",
        description="3 knives",
        condition="good",
        valuation_median_usd=30.0,
        trade_value_credits=30.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )
    svc._credit_store.earn_credits("bob", "previous-trade", 20.0)

    match = svc.propose_trade(
        listing_id=alice_listing["id"],
        requester_id="bob",
        offered_listing_id=bob_listing["id"],
        use_credits=True,
        credit_amount=20.0,
    )
    assert match["use_credits"] is True
    assert match["credit_amount"] == 20.0

    result = svc.accept_trade(match["id"], user_id="alice")
    assert result["status"] == "completed"
    assert svc._credit_store.get_credit_balance("bob") == 0.0
    assert svc._credit_store.get_credit_balance("alice") == 20.0


def test_cannot_trade_with_self():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    listing = svc.create_listing(
        user_id="alice",
        item_label="paint set",
        description="...",
        condition="good",
        valuation_median_usd=40.0,
        trade_value_credits=40.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )

    try:
        svc.propose_trade(
            listing_id=listing["id"],
            requester_id="alice",
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot trade with yourself" in str(e)


def test_decline_trade_releases_listing():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    alice_listing = svc.create_listing(
        user_id="alice",
        item_label="paint set",
        description="...",
        condition="good",
        valuation_median_usd=40.0,
        trade_value_credits=40.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )

    match = svc.propose_trade(
        listing_id=alice_listing["id"],
        requester_id="bob",
    )
    assert match["status"] == "pending"

    result = svc.decline_trade(match["id"], user_id="alice")
    assert result["status"] == "declined"

    listing_after = svc._get_listing(alice_listing["id"])
    assert listing_after["status"] == "available"
