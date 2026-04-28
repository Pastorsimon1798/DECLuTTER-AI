import os
import tempfile

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_service import TradeService


def test_create_trade_listing():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    listing = svc.create_listing(
        user_id="user-123",
        item_label="winsor newton oil paint set",
        description="12 tubes, barely used",
        condition="good",
        valuation_median_usd=35.0,
        trade_value_credits=35.0,
        latitude=43.6532,
        longitude=-79.3832,
        images=["img1.jpg"],
    )
    assert listing["item_label"] == "winsor newton oil paint set"
    assert listing["trade_value_credits"] == 35.0
    assert listing["status"] == "available"


def test_find_nearby_listings():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    svc.create_listing(
        user_id="user-123",
        item_label="oil paint set",
        description="...",
        condition="good",
        valuation_median_usd=35.0,
        trade_value_credits=35.0,
        latitude=43.6532,
        longitude=-79.3832,
        images=[],
    )
    results = svc.find_nearby(
        latitude=43.65,
        longitude=-79.38,
        radius_km=10.0,
    )
    assert len(results) >= 1
    assert results[0]["distance_km"] is not None


def test_exclude_own_listings():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    svc.create_listing(
        user_id="alice",
        item_label="paint set",
        description="...",
        condition="good",
        valuation_median_usd=35.0,
        trade_value_credits=35.0,
        latitude=43.65,
        longitude=-79.38,
        images=[],
    )
    results = svc.find_nearby(
        latitude=43.65,
        longitude=-79.38,
        radius_km=10.0,
        exclude_user_id="alice",
    )
    assert len(results) == 0
