from __future__ import annotations

import os
import sqlite3
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CreditTransaction:
    user_id: str
    amount: float
    trade_id: str
    item_label: str
    direction: str  # "earned" or "spent"
    created_at: str


class TradeCreditStore:
    """SQLite-backed credit ledger for trade transactions.

    Credits are non-monetary and cannot be purchased with cash.
    1 credit = $1 of fair trade value from the valuation engine.
    """

    def __init__(self, db_path: str | None = None) -> None:
        raw_path = db_path or os.getenv(
            "DECLUTTER_TRADE_DB_PATH",
            os.getenv("DECLUTTER_SESSION_DB_PATH", "/tmp/declutter_ai_trade.sqlite3"),
        )
        self.db_path = Path(raw_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if "/tmp/" in str(self.db_path):
            warnings.warn(
                f"TradeCreditStore is using a temporary path ({self.db_path}).",
                RuntimeWarning,
                stacklevel=2,
            )
        self._ensure_schema()

    def get_credit_balance(self, user_id: str) -> float:
        with self._db() as conn:
            earned = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM credit_transactions
                WHERE user_id = ? AND direction = 'earned'
                """,
                (user_id,),
            ).fetchone()["total"]

            spent = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) as total
                FROM credit_transactions
                WHERE user_id = ? AND direction = 'spent'
                """,
                (user_id,),
            ).fetchone()["total"]

        return round(float(earned) - float(spent), 2)

    def earn_credits(
        self, user_id: str, item_label: str, amount: float, trade_id: str = ""
    ) -> CreditTransaction:
        return self._record(user_id, amount, trade_id, item_label, "earned")

    def spend_credits(
        self, user_id: str, item_label: str, amount: float, trade_id: str = ""
    ) -> CreditTransaction:
        balance = self.get_credit_balance(user_id)
        if amount > balance:
            raise ValueError(
                f"Insufficient credits: {amount} requested, {balance} available"
            )
        return self._record(user_id, amount, trade_id, item_label, "spent")

    def _record(
        self, user_id: str, amount: float, trade_id: str, item_label: str, direction: str
    ) -> CreditTransaction:
        now = datetime.now(timezone.utc).isoformat()
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO credit_transactions (
                    user_id, amount, trade_id, item_label, direction, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, amount, trade_id, item_label, direction, now),
            )
        return CreditTransaction(
            user_id=user_id,
            amount=amount,
            trade_id=trade_id,
            item_label=item_label,
            direction=direction,
            created_at=now,
        )

    def get_transaction_history(
        self, user_id: str, limit: int = 50
    ) -> list[CreditTransaction]:
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT user_id, amount, trade_id, item_label, direction, created_at
                FROM credit_transactions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [
            CreditTransaction(
                user_id=r["user_id"],
                amount=r["amount"],
                trade_id=r["trade_id"],
                item_label=r["item_label"],
                direction=r["direction"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def _ensure_schema(self) -> None:
        with self._db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    trade_id TEXT,
                    item_label TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK(direction IN ('earned', 'spent')),
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_credits_user
                ON credit_transactions(user_id)
                """
            )

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
