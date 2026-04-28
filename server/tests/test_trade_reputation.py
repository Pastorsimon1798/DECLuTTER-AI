import os
import tempfile

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_service import TradeService


def test_rate_trade_partner():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    alice_listing = svc.create_listing(
        user_id="alice",
        item_label="paint set",
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
        item_label="brushes",
        description="assorted",
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
    svc.accept_trade(match["id"], user_id="alice")

    profile = svc.rate_user(
        trade_match_id=match["id"],
        rated_user_id="bob",
        rater_user_id="alice",
        rating=5,
        tags=["on_time", "accurate_description"],
        comment="Item was exactly as described",
    )
    assert profile["average_rating"] == 5.0
    assert profile["total_trades"] == 1
    assert "on_time" in profile["top_tags"]


def test_cannot_rate_self():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    try:
        svc.rate_user(
            trade_match_id="m1",
            rated_user_id="alice",
            rater_user_id="alice",
            rating=5,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot rate yourself" in str(e)


def test_rating_must_be_1_to_5():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    try:
        svc.rate_user(
            trade_match_id="m1",
            rated_user_id="bob",
            rater_user_id="alice",
            rating=6,
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Rating must be between 1 and 5" in str(e)


def test_reputation_aggregation():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))

    for i in range(3):
        listing = svc.create_listing(
            user_id="alice",
            item_label=f"item-{i}",
            condition="good",
            valuation_median_usd=10.0,
            trade_value_credits=10.0,
            latitude=43.65,
            longitude=-79.38,
            images=[],
        )
        match = svc.propose_trade(listing_id=listing["id"], requester_id="bob")
        svc.accept_trade(match["id"], user_id="alice")
        svc.rate_user(
            trade_match_id=match["id"],
            rated_user_id="bob",
            rater_user_id="alice",
            rating=4,
            tags=["friendly"],
        )

    profile = svc.get_reputation("bob")
    assert profile["average_rating"] == 4.0
    assert profile["total_trades"] == 3
    assert "friendly" in profile["top_tags"]
