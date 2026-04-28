import os
os.environ['DECLUTTER_RATE_LIMIT_DISABLED'] = '1'

from fastapi.testclient import TestClient

from app.main import app
from security import dependencies
from services.trade_service import TradeService

client = TestClient(app)

VALID_HEADERS = {
    'Authorization': 'Bearer test-user-token',
    'X-Firebase-AppCheck': 'test-app-check-token',
}


def _set_auth_mode(mode: str) -> None:
    for key in [
        'DECLUTTER_AUTH_MODE',
        'DECLUTTER_SHARED_ACCESS_TOKEN',
        'DECLUTTER_TEST_ID_TOKEN',
        'DECLUTTER_TEST_APP_CHECK_TOKEN',
    ]:
        os.environ.pop(key, None)
    os.environ['DECLUTTER_AUTH_MODE'] = mode
    if mode == 'scaffold':
        os.environ['DECLUTTER_TEST_ID_TOKEN'] = 'test-user-token'
        os.environ['DECLUTTER_TEST_APP_CHECK_TOKEN'] = 'test-app-check-token'
    dependencies.get_firebase_verifier.cache_clear()


def _fresh_trade_service() -> TradeService:
    import tempfile
    db_path = tempfile.mktemp(suffix=".sqlite3")
    os.environ['DECLUTTER_TRADE_DB_PATH'] = db_path
    # Clear the cached service so a new one is created with the new path
    from api.routes.trade import get_trade_service
    get_trade_service.cache_clear()
    return TradeService(db_path=db_path)


def test_trade_listing_lifecycle():
    _set_auth_mode('scaffold')
    r = client.post(
        "/trade/listings",
        headers=VALID_HEADERS,
        json={
            "item_label": "watercolor set",
            "description": "24 pan set",
            "condition": "good",
            "valuation_median_usd": 25.0,
            "trade_value_credits": 25.0,
            "latitude": 43.65,
            "longitude": -79.38,
            "images": [],
            "tags": ["art", "paint"],
        },
    )
    assert r.status_code == 200
    listing = r.json()
    assert listing["status"] == "available"
    assert listing["trade_value_credits"] == 25.0
    assert listing["user_id"] == "scaffold-user"

    # Nearby search should return 200; empty because own listing is excluded
    r = client.get(
        "/trade/listings/nearby?latitude=43.65&longitude=-79.38&radius_km=10",
        headers=VALID_HEADERS,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_trade_match_flow():
    _set_auth_mode('scaffold')
    svc = _fresh_trade_service()

    # Create a listing directly for "other-user" so scaffold-user can propose
    other_listing = svc.create_listing(
        user_id="other-user",
        item_label="sketchbook",
        description="A4",
        condition="good",
        valuation_median_usd=15.0,
        trade_value_credits=15.0,
        latitude=43.65,
        longitude=-79.38,
    )

    # Propose trade via API as scaffold-user
    r = client.post("/trade/matches", headers=VALID_HEADERS, json={
        "listing_id": other_listing["id"],
        "message": "Want to trade?",
        "use_credits": False,
        "credit_amount": 0,
    })
    assert r.status_code == 200
    match = r.json()
    assert match["status"] == "pending"
    assert match["requester_id"] == "scaffold-user"
    assert match["owner_id"] == "other-user"

    # Other user cannot decline (decline requires owner)
    # But scaffold-user is requester, not owner
    r = client.post(f"/trade/matches/{match['id']}/decline", headers=VALID_HEADERS)
    assert r.status_code == 400

    # Now set up a match where scaffold-user is the owner so they can accept
    own_listing = svc.create_listing(
        user_id="scaffold-user",
        item_label="charcoal pencils",
        description="12 pack",
        condition="new",
        valuation_median_usd=15.0,
        trade_value_credits=15.0,
        latitude=43.65,
        longitude=-79.38,
    )
    match2 = svc.propose_trade(
        listing_id=own_listing["id"],
        requester_id="other-user",
        message="Interested",
    )

    r = client.post(f"/trade/matches/{match2['id']}/accept", headers=VALID_HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


def test_trade_credit_balance():
    _set_auth_mode('scaffold')
    r = client.get("/trade/credits", headers=VALID_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert "balance" in body
    assert "transactions" in body
    assert isinstance(body["balance"], float)
    assert isinstance(body["transactions"], list)


def test_trade_propose_self_trade_fails():
    _set_auth_mode('scaffold')
    svc = _fresh_trade_service()
    own_listing = svc.create_listing(
        user_id="scaffold-user",
        item_label="guitar",
        condition="good",
        valuation_median_usd=100.0,
        trade_value_credits=100.0,
        latitude=43.65,
        longitude=-79.38,
    )
    r = client.post("/trade/matches", headers=VALID_HEADERS, json={
        "listing_id": own_listing["id"],
        "message": "I'll trade with myself",
    })
    assert r.status_code == 400


def test_trade_nearby_excludes_own_and_includes_others():
    _set_auth_mode('scaffold')
    svc = _fresh_trade_service()

    # Create own listing via API
    client.post("/trade/listings", headers=VALID_HEADERS, json={
        "item_label": "my item",
        "condition": "good",
        "valuation_median_usd": 10.0,
        "trade_value_credits": 10.0,
        "latitude": 43.65,
        "longitude": -79.38,
    })

    # Create another user's listing directly
    svc.create_listing(
        user_id="neighbor",
        item_label="neighbor item",
        condition="good",
        valuation_median_usd=10.0,
        trade_value_credits=10.0,
        latitude=43.65,
        longitude=-79.38,
    )

    r = client.get(
        "/trade/listings/nearby?latitude=43.65&longitude=-79.38&radius_km=10",
        headers=VALID_HEADERS,
    )
    assert r.status_code == 200
    results = r.json()
    neighbor_results = [r for r in results if r["user_id"] == "neighbor"]
    assert len(neighbor_results) == 1
    assert neighbor_results[0]["item_label"] == "neighbor item"
