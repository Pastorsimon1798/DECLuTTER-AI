import os
import tempfile

os.environ.setdefault("DECLUTTER_ENV", "test")

from models.trade import TradeCreditStore


def test_user_starts_with_zero_credits():
    store = TradeCreditStore(db_path=tempfile.mktemp(suffix=".sqlite3"))
    assert store.get_credit_balance("user-123") == 0.0


def test_credits_earned_from_trade_value():
    store = TradeCreditStore(db_path=tempfile.mktemp(suffix=".sqlite3"))
    store.earn_credits("user-123", "acrylic paint set", 45.0)
    assert store.get_credit_balance("user-123") == 45.0


def test_credits_spent_on_trade():
    store = TradeCreditStore(db_path=tempfile.mktemp(suffix=".sqlite3"))
    store.earn_credits("user-123", "item-a", 50.0)
    store.spend_credits("user-123", "item-b", 30.0)
    assert store.get_credit_balance("user-123") == 20.0


def test_insufficient_credits_raises():
    store = TradeCreditStore(db_path=tempfile.mktemp(suffix=".sqlite3"))
    store.earn_credits("user-123", "item-a", 10.0)
    try:
        store.spend_credits("user-123", "item-b", 30.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Insufficient credits" in str(e)


def test_transaction_history():
    store = TradeCreditStore(db_path=tempfile.mktemp(suffix=".sqlite3"))
    store.earn_credits("user-123", "paint set", 40.0, trade_id="t1")
    store.spend_credits("user-123", "brushes", 15.0, trade_id="t2")
    history = store.get_transaction_history("user-123")
    assert len(history) == 2
    assert history[0].direction == "spent"
    assert history[0].amount == 15.0
    assert history[1].direction == "earned"
    assert history[1].amount == 40.0
