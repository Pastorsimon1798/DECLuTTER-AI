import os
import tempfile

os.environ.setdefault("DECLUTTER_ENV", "test")

from services.trade_service import TradeService


def test_verify_user_email():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    result = svc.verify_user(user_id="alice", method="email")
    assert result["verified"] is True
    assert result["verification_method"] == "email"
    assert result["verified_at"] is not None


def test_verify_user_phone():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    result = svc.verify_user(user_id="bob", method="phone")
    assert result["verified"] is True
    assert result["verification_method"] == "phone"


def test_unverified_user():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    result = svc.get_verification_status("unknown")
    assert result["verified"] is False
    assert result["verified_at"] is None


def test_invalid_method_raises():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    try:
        svc.verify_user(user_id="alice", method="smoke_signal")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "email, phone, or id" in str(e)


def test_verification_overwrite():
    svc = TradeService(db_path=tempfile.mktemp(suffix=".sqlite3"))
    svc.verify_user(user_id="alice", method="email")
    result = svc.verify_user(user_id="alice", method="phone")
    assert result["verification_method"] == "phone"
