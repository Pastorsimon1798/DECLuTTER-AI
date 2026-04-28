# Barter/Trade Marketplace Implementation Plan

**Goal:** Build a "Fair Trade" mode into the existing declutter app that lets users trade items using the valuation engine as a fairness backbone. All categories from day one. NeuroDivergent-friendly UX throughout.

**Architecture:** Extend the existing FastAPI backend with trade-specific models (trade listings, credits, matches, reputation), add trade endpoints alongside existing selling flows, and build a trade UI in the Flutter app. The valuation engine (4,018 seeded items + LLM fallback) becomes the "fair trade value" reference for every item.

**Tech Stack:** FastAPI + SQLite (backend), Flutter (mobile), existing valuation engine + LLM fallback, local-first with optional shipping integration.

---

## Phase 1: Core Trade Infrastructure + ALL Categories (0–3 months)

### What's in Phase 1

Everything that makes the trade system work for **any item type**: artist supplies, books, plants, games, baby gear, disability equipment, electronics, clothes — all of it. The same listing, matching, credit, and reputation system handles every category.

**What's NOT in Phase 1:** Revenue features (verified badges, shipping labels), advanced matching algorithms, nonprofit integrations, distributed moderation at scale. Those come in Phase 2.

---

### Task 1: Trade Credit System Schema

**Files:**
- Create: `server/app/models/trade.py`
- Test: `server/tests/test_trade_credits.py`

**Step 1: Write the failing test**

```python
def test_user_starts_with_zero_credits():
    from services.trade_service import TradeService
    svc = TradeService()
    assert svc.get_credit_balance("user-123") == 0.0

def test_credits_earned_from_trade_value():
    from services.trade_service import TradeService
    svc = TradeService()
    svc.earn_credits("user-123", "acrylic paint set", 45.0)
    assert svc.get_credit_balance("user-123") == 45.0

def test_credits_spent_on_trade():
    from services.trade_service import TradeService
    svc = TradeService()
    svc.earn_credits("user-123", "item-a", 50.0)
    svc.spend_credits("user-123", "item-b", 30.0)
    assert svc.get_credit_balance("user-123") == 20.0
```

**Step 2: Run test to verify it fails**

Run: `cd server && pytest tests/test_trade_credits.py -v`
Expected: FAIL with "module not found"

**Step 3: Write minimal implementation**

Create `server/app/models/trade.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `cd server && pytest tests/test_trade_credits.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add server/app/models/trade.py server/tests/test_trade_credits.py
git commit -m "feat: trade credit ledger schema and basic operations"
```

---

### Task 2: Trade Listing & Matching Service

**Files:**
- Create: `server/app/schemas/trade.py`
- Create: `server/app/services/trade_service.py`
- Test: `server/tests/test_trade_listings.py`
- Test: `server/tests/test_trade_service.py`

**Step 1: Write the failing tests**

```python
# test_trade_listings.py
def test_create_trade_listing():
    from services.trade_service import TradeService
    svc = TradeService()
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
    from services.trade_service import TradeService
    svc = TradeService()
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

# test_trade_service.py
def test_propose_trade_with_exact_match():
    from services.trade_service import TradeService
    svc = TradeService()

    alice_listing = svc.create_listing(
        user_id="alice", item_label="acrylic paint set",
        description="24 colors", condition="good",
        valuation_median_usd=40.0, trade_value_credits=40.0,
        latitude=43.65, longitude=-79.38, images=[],
    )
    bob_listing = svc.create_listing(
        user_id="bob", item_label="paint brushes",
        description="assorted sizes", condition="good",
        valuation_median_usd=40.0, trade_value_credits=40.0,
        latitude=43.65, longitude=-79.38, images=[],
    )

    match = svc.propose_trade(
        listing_id=alice_listing["id"],
        requester_id="bob",
        offered_listing_id=bob_listing["id"],
    )
    assert match["status"] == "pending"

    result = svc.accept_trade(match["id"], user_id="alice")
    assert result["status"] == "completed"

def test_propose_trade_with_credit_top_up():
    from services.trade_service import TradeService
    svc = TradeService()

    alice_listing = svc.create_listing(
        user_id="alice", item_label="canvas set",
        description="5 stretched canvases", condition="good",
        valuation_median_usd=50.0, trade_value_credits=50.0,
        latitude=43.65, longitude=-79.38, images=[],
    )
    bob_listing = svc.create_listing(
        user_id="bob", item_label="palette knives",
        description="3 knives", condition="good",
        valuation_median_usd=30.0, trade_value_credits=30.0,
        latitude=43.65, longitude=-79.38, images=[],
    )
    svc._credit_store.earn_credits("bob", "previous-trade", 20.0)

    match = svc.propose_trade(
        listing_id=alice_listing["id"],
        requester_id="bob",
        offered_listing_id=bob_listing["id"],
        use_credits=True, credit_amount=20.0,
    )
    assert match["use_credits"] is True
    assert match["credit_amount"] == 20.0
```

**Step 2: Run tests to verify they fail**

Run: `cd server && pytest tests/test_trade_listings.py tests/test_trade_service.py -v`
Expected: FAIL

**Step 3: Write minimal implementations**

Create `server/app/schemas/trade.py`:

```python
from pydantic import BaseModel, Field


class TradeListingRequest(BaseModel):
    item_label: str = Field(min_length=1)
    description: str = Field(default="", max_length=2000)
    condition: str = Field(default="good")
    valuation_median_usd: float = Field(ge=0)
    trade_value_credits: float = Field(ge=0)
    latitude: float | None = None
    longitude: float | None = None
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    wants_in_return: list[str] = Field(default_factory=list)


class TradeListingResponse(BaseModel):
    id: str
    user_id: str
    item_label: str
    description: str
    condition: str
    valuation_median_usd: float
    trade_value_credits: float
    latitude: float | None = None
    longitude: float | None = None
    images: list[str]
    tags: list[str]
    wants_in_return: list[str]
    status: str
    created_at: str
    updated_at: str
    distance_km: float | None = None


class TradeMatchRequest(BaseModel):
    listing_id: str
    offered_listing_id: str | None = None
    message: str = Field(default="", max_length=1000)
    use_credits: bool = False
    credit_amount: float = Field(default=0.0, ge=0)


class TradeMatchResponse(BaseModel):
    id: str
    listing_id: str
    requester_id: str
    owner_id: str
    offered_listing_id: str | None = None
    message: str
    use_credits: bool
    credit_amount: float
    status: str
    created_at: str
    updated_at: str
```

Create `server/app/services/trade_service.py`:

```python
from __future__ import annotations

import json
import math
import os
import sqlite3
import uuid
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from models.trade import TradeCreditStore


class TradeService:
    """Core trade matching and execution service."""

    def __init__(
        self,
        db_path: str | None = None,
        credit_store: TradeCreditStore | None = None,
    ) -> None:
        raw_path = db_path or os.getenv(
            "DECLUTTER_TRADE_DB_PATH",
            os.getenv("DECLUTTER_SESSION_DB_PATH", "/tmp/declutter_ai_trade.sqlite3"),
        )
        self.db_path = Path(raw_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._credit_store = credit_store or TradeCreditStore(db_path=str(self.db_path))
        self._ensure_schema()

    def create_listing(
        self,
        user_id: str,
        item_label: str,
        description: str = "",
        condition: str = "good",
        valuation_median_usd: float = 0.0,
        trade_value_credits: float = 0.0,
        latitude: float | None = None,
        longitude: float | None = None,
        images: list[str] | None = None,
        tags: list[str] | None = None,
        wants_in_return: list[str] | None = None,
    ) -> dict[str, Any]:
        listing_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()

        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO trade_listings (
                    id, user_id, item_label, description, condition,
                    valuation_median_usd, trade_value_credits,
                    latitude, longitude, images, tags, wants_in_return,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing_id, user_id, item_label, description, condition,
                    valuation_median_usd, trade_value_credits,
                    latitude, longitude,
                    json.dumps(images or []),
                    json.dumps(tags or []),
                    json.dumps(wants_in_return or []),
                    "available", now, now,
                ),
            )
        return self._listing_to_dict(listing_id)

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        exclude_user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT * FROM trade_listings
                WHERE status = 'available'
                AND latitude IS NOT NULL AND longitude IS NOT NULL
                """
            ).fetchall()

        results = []
        for row in rows:
            if exclude_user_id and row["user_id"] == exclude_user_id:
                continue
            dist = self._haversine(
                latitude, longitude, row["latitude"], row["longitude"]
            )
            if dist <= radius_km:
                d = self._row_to_dict(row)
                d["distance_km"] = round(dist, 2)
                results.append(d)

        results.sort(key=lambda x: x["distance_km"])
        return results

    def propose_trade(
        self,
        listing_id: str,
        requester_id: str,
        offered_listing_id: str | None = None,
        message: str = "",
        use_credits: bool = False,
        credit_amount: float = 0.0,
    ) -> dict[str, Any]:
        listing = self._get_listing(listing_id)
        if listing is None:
            raise ValueError(f"Listing {listing_id} not found")
        if listing["status"] != "available":
            raise ValueError("Listing is not available for trade")
        if listing["user_id"] == requester_id:
            raise ValueError("Cannot trade with yourself")

        if use_credits and credit_amount > 0:
            balance = self._credit_store.get_credit_balance(requester_id)
            if credit_amount > balance:
                raise ValueError(f"Insufficient credits: {credit_amount} > {balance}")

        match_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()

        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO trade_matches (
                    id, listing_id, requester_id, owner_id,
                    offered_listing_id, message, use_credits, credit_amount,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    match_id, listing_id, requester_id, listing["user_id"],
                    offered_listing_id, message, use_credits, credit_amount,
                    "pending", now, now,
                ),
            )
            conn.execute(
                "UPDATE trade_listings SET status = ?, updated_at = ? WHERE id = ?",
                ("pending", now, listing_id),
            )

        return self._match_to_dict(match_id)

    def accept_trade(self, match_id: str, user_id: str) -> dict[str, Any]:
        match = self._get_match(match_id)
        if match is None:
            raise ValueError(f"Trade match {match_id} not found")
        if match["owner_id"] != user_id:
            raise ValueError("Only the listing owner can accept")
        if match["status"] != "pending":
            raise ValueError("Trade is not pending")

        now = datetime.now(timezone.utc).isoformat()

        with self._db() as conn:
            if match["use_credits"] and match["credit_amount"] > 0:
                self._credit_store.spend_credits(
                    match["requester_id"], match["listing_id"],
                    match["credit_amount"], trade_id=match_id,
                )
                self._credit_store.earn_credits(
                    match["owner_id"], match["listing_id"],
                    match["credit_amount"], trade_id=match_id,
                )

            conn.execute(
                "UPDATE trade_matches SET status = ?, updated_at = ? WHERE id = ?",
                ("completed", now, match_id),
            )
            conn.execute(
                "UPDATE trade_listings SET status = ?, updated_at = ? WHERE id = ?",
                ("completed", now, match["listing_id"]),
            )
            if match["offered_listing_id"]:
                conn.execute(
                    "UPDATE trade_listings SET status = ?, updated_at = ? WHERE id = ?",
                    ("completed", now, match["offered_listing_id"]),
                )

        return self._match_to_dict(match_id)

    def decline_trade(self, match_id: str, user_id: str) -> dict[str, Any]:
        match = self._get_match(match_id)
        if match is None:
            raise ValueError(f"Trade match {match_id} not found")
        if match["owner_id"] != user_id:
            raise ValueError("Only the listing owner can decline")
        if match["status"] != "pending":
            raise ValueError("Trade is not pending")

        now = datetime.now(timezone.utc).isoformat()

        with self._db() as conn:
            conn.execute(
                "UPDATE trade_matches SET status = ?, updated_at = ? WHERE id = ?",
                ("declined", now, match_id),
            )
            conn.execute(
                "UPDATE trade_listings SET status = ?, updated_at = ? WHERE id = ?",
                ("available", now, match["listing_id"]),
            )

        return self._match_to_dict(match_id)

    def _get_listing(self, listing_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM trade_listings WHERE id = ?", (listing_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def _get_match(self, match_id: str) -> dict[str, Any] | None:
        with self._db() as conn:
            row = conn.execute(
                "SELECT * FROM trade_matches WHERE id = ?", (match_id,)
            ).fetchone()
        return self._match_row_to_dict(row) if row else None

    def _listing_to_dict(self, listing_id: str) -> dict[str, Any]:
        row = self._get_listing(listing_id)
        if row is None:
            raise RuntimeError("Listing not found after insert")
        return row

    def _match_to_dict(self, match_id: str) -> dict[str, Any]:
        row = self._get_match(match_id)
        if row is None:
            raise RuntimeError("Match not found after insert")
        return row

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "item_label": row["item_label"],
            "description": row["description"],
            "condition": row["condition"],
            "valuation_median_usd": row["valuation_median_usd"],
            "trade_value_credits": row["trade_value_credits"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "images": json.loads(row["images"]),
            "tags": json.loads(row["tags"]),
            "wants_in_return": json.loads(row["wants_in_return"]),
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _match_row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "listing_id": row["listing_id"],
            "requester_id": row["requester_id"],
            "owner_id": row["owner_id"],
            "offered_listing_id": row["offered_listing_id"],
            "message": row["message"],
            "use_credits": bool(row["use_credits"]),
            "credit_amount": row["credit_amount"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = (
            math.sin(dphi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _ensure_schema(self) -> None:
        with self._db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_listings (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    item_label TEXT NOT NULL,
                    description TEXT,
                    condition TEXT,
                    valuation_median_usd REAL,
                    trade_value_credits REAL,
                    latitude REAL,
                    longitude REAL,
                    images TEXT,
                    tags TEXT,
                    wants_in_return TEXT,
                    status TEXT NOT NULL DEFAULT 'available',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_listings_status ON trade_listings(status)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_matches (
                    id TEXT PRIMARY KEY,
                    listing_id TEXT NOT NULL,
                    requester_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    offered_listing_id TEXT,
                    message TEXT,
                    use_credits INTEGER DEFAULT 0,
                    credit_amount REAL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_matches_listing ON trade_matches(listing_id)"
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
```

**Step 4: Run tests to verify they pass**

Run: `cd server && pytest tests/test_trade_listings.py tests/test_trade_service.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add server/app/schemas/trade.py server/app/services/trade_service.py server/tests/test_trade_listings.py server/tests/test_trade_service.py
git commit -m "feat: trade listing and matching service with credit support"
```

---

### Task 3: Trade API Routes

**Files:**
- Create: `server/app/api/routes/trade.py`
- Modify: `server/app/main.py` (include trade router)
- Test: `server/tests/test_trade_api.py`

**Step 1: Write the failing test**

```python
def test_trade_listing_lifecycle():
    _set_auth_mode('scaffold')

    r = client.post(
        '/trade/listings',
        headers=VALID_HEADERS,
        json={
            'item_label': 'watercolor set',
            'description': '24 pan set',
            'condition': 'good',
            'valuation_median_usd': 25.0,
            'trade_value_credits': 25.0,
            'latitude': 43.65,
            'longitude': -79.38,
            'images': [],
            'tags': ['art', 'paint'],
        },
    )
    assert r.status_code == 200
    listing = r.json()
    assert listing['status'] == 'available'

    r = client.get(
        '/trade/listings/nearby?latitude=43.65&longitude=-79.38&radius_km=10',
        headers=VALID_HEADERS,
    )
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_trade_match_flow():
    _set_auth_mode('scaffold')

    r = client.post('/trade/listings', headers=VALID_HEADERS, json={
        'item_label': 'charcoal pencils', 'description': '12 pack',
        'condition': 'new', 'valuation_median_usd': 15.0,
        'trade_value_credits': 15.0, 'latitude': 43.65,
        'longitude': -79.38, 'images': [],
    })
    alice_listing = r.json()

    r = client.post('/trade/listings', headers=VALID_HEADERS, json={
        'item_label': 'sketchbook', 'description': 'A4',
        'condition': 'good', 'valuation_median_usd': 15.0,
        'trade_value_credits': 15.0, 'latitude': 43.65,
        'longitude': -79.38, 'images': [],
    })
    bob_listing = r.json()

    r = client.post('/trade/matches', headers=VALID_HEADERS, json={
        'listing_id': alice_listing['id'],
        'offered_listing_id': bob_listing['id'],
        'message': 'Want to trade?',
        'use_credits': False, 'credit_amount': 0,
    })
    assert r.status_code == 200
    match = r.json()
    assert match['status'] == 'pending'

    r = client.post(f'/trade/matches/{match["id"]}/accept', headers=VALID_HEADERS)
    assert r.status_code == 200
    assert r.json()['status'] == 'completed'
```

**Step 2: Run test to verify it fails**

Run: `cd server && pytest tests/test_trade_api.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `server/app/api/routes/trade.py`:

```python
from functools import lru_cache

from fastapi import APIRouter, Depends

from schemas.trade import (
    TradeListingRequest, TradeListingResponse,
    TradeMatchRequest, TradeMatchResponse,
)
from services.trade_service import TradeService

router = APIRouter(prefix="/trade", tags=["trade"])


@lru_cache(maxsize=1)
def get_trade_service() -> TradeService:
    return TradeService()


@router.post("/listings", response_model=TradeListingResponse)
def create_listing(
    payload: TradeListingRequest,
    service: TradeService = Depends(get_trade_service),
) -> TradeListingResponse:
    result = service.create_listing(
        user_id="current-user",
        item_label=payload.item_label,
        description=payload.description,
        condition=payload.condition,
        valuation_median_usd=payload.valuation_median_usd,
        trade_value_credits=payload.trade_value_credits,
        latitude=payload.latitude,
        longitude=payload.longitude,
        images=payload.images,
        tags=payload.tags,
        wants_in_return=payload.wants_in_return,
    )
    return TradeListingResponse(**result)


@router.get("/listings/nearby")
def find_nearby(
    latitude: float, longitude: float, radius_km: float = 5.0,
    service: TradeService = Depends(get_trade_service),
) -> list[TradeListingResponse]:
    results = service.find_nearby(
        latitude=latitude, longitude=longitude,
        radius_km=radius_km, exclude_user_id="current-user",
    )
    return [TradeListingResponse(**r) for r in results]


@router.post("/matches", response_model=TradeMatchResponse)
def propose_trade(
    payload: TradeMatchRequest,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    result = service.propose_trade(
        listing_id=payload.listing_id,
        requester_id="current-user",
        offered_listing_id=payload.offered_listing_id,
        message=payload.message,
        use_credits=payload.use_credits,
        credit_amount=payload.credit_amount,
    )
    return TradeMatchResponse(**result)


@router.post("/matches/{match_id}/accept", response_model=TradeMatchResponse)
def accept_trade(
    match_id: str,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    result = service.accept_trade(match_id, user_id="current-user")
    return TradeMatchResponse(**result)


@router.post("/matches/{match_id}/decline", response_model=TradeMatchResponse)
def decline_trade(
    match_id: str,
    service: TradeService = Depends(get_trade_service),
) -> TradeMatchResponse:
    result = service.decline_trade(match_id, user_id="current-user")
    return TradeMatchResponse(**result)


@router.get("/credits")
def get_credit_balance(
    service: TradeService = Depends(get_trade_service),
) -> dict:
    balance = service._credit_store.get_credit_balance("current-user")
    history = service._credit_store.get_transaction_history("current-user", limit=20)
    return {
        "balance": balance,
        "transactions": [
            {"amount": t.amount, "item_label": t.item_label,
             "direction": t.direction, "created_at": t.created_at}
            for t in history
        ],
    }
```

Modify `server/app/main.py`:

```python
from api.routes.trade import router as trade_router
# In create_app():
api.include_router(trade_router, dependencies=protected)
```

**Step 4: Run test to verify it passes**

Run: `cd server && pytest tests/test_trade_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add server/app/api/routes/trade.py server/app/main.py server/tests/test_trade_api.py
git commit -m "feat: trade API routes for listings, matching, and credits"
```

---

### Task 4: ND-Specific UX (Templates, Checklists, Rules)

**Files:**
- Create: `server/app/services/trade_templates.py`
- Modify: `server/app/api/routes/trade.py`
- Test: `server/tests/test_trade_nd_ux.py`

**Step 1: Write the failing test**

```python
def test_trade_message_templates():
    from services.trade_templates import get_message_templates
    templates = get_message_templates("propose")
    assert len(templates) >= 3
    assert "trade" in templates[0].lower()

def test_condition_checklist():
    from services.trade_templates import get_condition_checklist
    checklist = get_condition_checklist("good")
    assert "no major damage" in checklist
    assert isinstance(checklist, list)

def test_trade_rules():
    from services.trade_templates import get_trade_rules
    rules = get_trade_rules()
    assert len(rules) >= 4
    assert "trade value" in rules[0].lower()
```

**Step 2: Run test to verify it fails**

Run: `cd server && pytest tests/test_trade_nd_ux.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Create `server/app/services/trade_templates.py`:

```python
"""NeuroDivergent-friendly trade templates and structured interactions.

Design principles:
- Literal, explicit language (no idioms, no ambiguity)
- Fixed options instead of free-text where possible
- Async-friendly (no real-time negotiation pressure)
- Clear expectations at every step
"""


MESSAGE_TEMPLATES = {
    "propose": [
        "I would like to propose a trade for your [item]. I have [my item] valued at [value]. Would you be interested?",
        "I am interested in your [item]. I can offer [my item] plus [credit amount] credits. Let me know if this works.",
        "I would like to trade [my item] for your [item]. Both are valued at approximately [value]. Would you accept?",
    ],
    "accept": [
        "I accept your trade proposal. I will prepare the item for pickup/shipping.",
        "Trade accepted. Please let me know your preferred pickup time or shipping address.",
    ],
    "decline": [
        "Thank you for your interest, but I am not interested in this trade at this time.",
        "I appreciate the offer, but I am looking for different items right now.",
    ],
    "follow_up": [
        "Just checking in — are you still interested in our trade?",
        "I have the item ready. When would be a good time to meet?",
    ],
}


CONDITION_CHECKLISTS = {
    "new": [
        "Item is unopened or unused",
        "Original packaging intact",
        "No signs of wear",
    ],
    "like_new": [
        "Item used once or twice only",
        "No visible wear",
        "All parts/pieces included",
        "Original packaging available",
    ],
    "good": [
        "Item functions perfectly",
        "Minor cosmetic wear only",
        "No major damage",
        "All essential parts included",
    ],
    "fair": [
        "Item functions but has visible wear",
        "Some cosmetic damage",
        "May be missing non-essential parts",
        "Still usable",
    ],
    "for_parts": [
        "Item does not function fully",
        "Significant damage or wear",
        "Useful for parts, repair, or craft projects",
        "Condition clearly described",
    ],
}


TRADE_RULES = [
    "Both parties agree to the trade value shown.",
    "Items must match the described condition.",
    "Pickup or shipping must be arranged within 7 days.",
    "If using credits, the balance is deducted immediately upon acceptance.",
    "Either party can cancel before acceptance with no penalty.",
    "After acceptance, the trade is final.",
]


def get_message_templates(intent: str) -> list[str]:
    return MESSAGE_TEMPLATES.get(intent, [""])


def get_condition_checklist(condition: str) -> list[str]:
    return CONDITION_CHECKLISTS.get(condition, [])


def get_trade_rules() -> list[str]:
    return TRADE_RULES
```

Add to `server/app/api/routes/trade.py`:

```python
@router.get("/templates/{intent}")
def get_templates(intent: str) -> dict:
    from services.trade_templates import get_message_templates
    return {"intent": intent, "templates": get_message_templates(intent)}


@router.get("/conditions/{condition}")
def get_condition_details(condition: str) -> dict:
    from services.trade_templates import get_condition_checklist
    return {"condition": condition, "checklist": get_condition_checklist(condition)}


@router.get("/rules")
def get_trade_rules() -> dict:
    from services.trade_templates import get_trade_rules
    return {"rules": get_trade_rules()}
```

**Step 4: Run test to verify it passes**

Run: `cd server && pytest tests/test_trade_nd_ux.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add server/app/services/trade_templates.py server/tests/test_trade_nd_ux.py
git commit -m "feat: ND-friendly trade templates, condition checklists, and explicit rules"
```

---

### Task 5: Reputation System

**Files:**
- Modify: `server/app/services/trade_service.py`
- Test: `server/tests/test_trade_reputation.py`

**Step 1: Write the failing test**

```python
def test_rate_trade_partner():
    from services.trade_service import TradeService
    svc = TradeService()

    svc.rate_user(
        trade_match_id="match-123",
        rated_user_id="bob",
        rater_user_id="alice",
        rating=5,
        tags=["on_time", "accurate_description"],
        comment="Item was exactly as described",
    )

    profile = svc.get_reputation("bob")
    assert profile["average_rating"] == 5.0
    assert profile["total_trades"] == 1
    assert "on_time" in profile["top_tags"]
```

**Step 2–5:** Add `trade_reviews` table to schema, implement `rate_user()` and `get_reputation()`, test, commit.

---

### Task 6: Safety Checklists (Generic, All Categories)

**Files:**
- Create: `server/app/services/safety_checklists.py`
- Modify: `server/app/api/routes/trade.py`
- Test: `server/tests/test_trade_safety.py`

Safety checklists vary by item type but share a common structure. Examples:

- **Electronics:** "Works when plugged in," "No frayed cords," "Battery holds charge"
- **Baby gear:** "No recalls issued," "All straps/buckles intact," "Clean, no stains"
- **Disability equipment:** "Sanitized," "All adjustment mechanisms work," "No rust/corrosion"
- **Art supplies:** "Non-toxic label visible," "No dried-out tubes," "Brushes not shedding"
- **Plants:** "No visible pests," "Potted in clean soil," "Acclimated to indoor conditions"

Implementation: a tag-to-checklist mapping. When a listing has tag "baby", the safety endpoint returns the baby gear checklist.

---

### Task 7: Verified Trader Badges

**Files:**
- Modify: `server/app/services/trade_service.py` (add verified flag)
- Modify: `server/app/api/routes/trade.py` (add verification endpoints)
- Test: `server/tests/test_trade_verified.py`

**Implementation:**
- `verified` boolean on user profile
- `verified_at` timestamp
- `verification_method` ("email", "phone", "id")
- Phase 1: Self-attested verification (email confirm + phone SMS). Manual ID review queue.
- Phase 2: Stripe Identity integration for automated ID verification.
- Badge shown on listing cards.

---

### Task 8: Algorithmic Matching (Multi-Party Trade Loops)

**Files:**
- Create: `server/app/services/trade_matcher.py`
- Test: `server/tests/test_trade_matcher.py`

**Core algorithm:** Find trade cycles of length 2+ where:
- Alice wants Bob's item
- Bob wants Charlie's item
- Charlie wants Alice's item (or has credits)

This is a **directed graph cycle detection** problem. Build a graph where edges represent "user wants item owned by another user." Find cycles using DFS. Prioritize shortest cycles (2-party first, then 3-party, etc.).

**Step 1:** Build want-graph from listings
**Step 2:** Find all cycles up to length N (configurable, default 4)
**Step 3:** Score cycles by value match closeness
**Step 4:** Notify users: "We found a 3-way trade: you → Alice → Bob → you"

---

### Task 9: Expand Price Seed Database for ALL Categories

**Files:**
- Modify: `server/app/data/price_seed.json`

Add valuations for:
- Plants/seeds (seed packets, cuttings, pots, soil)
- Gaming (board games, TCG cards, video games, consoles)
- Baby gear (strollers, carriers, clothes by size, toys by age)
- Disability equipment (walkers, braces, wheelchairs, sensory tools)
- Books (by genre, textbooks)
- Clothing (by type, size)
- Electronics (by category)
- Sports gear (by sport, size)
- Musical instruments (by type)

Target: expand from 4,018 → 6,000+ items.

---

### Task 10: Flutter Trade UI

**Files:**
- Create: `app/lib/features/trade/screens/`
- Create: `app/lib/features/trade/widgets/`
- Create: `app/lib/features/trade/models/trade_models.dart`
- Modify: `app/lib/main.dart`

**Screens:**
1. **Browse Trades** — Map view + list view, filter by distance/category, condition badges
2. **Create Trade Listing** — "Trade instead of Sell" toggle after valuation, pre-filled trade value, condition checklist picker, template-based description helper
3. **Trade Detail** — Item info, fair value, condition checklist, safety checklist (if applicable), trade rules, "Propose Trade" with template picker, distance badge
4. **My Matches** — Pending/incoming trades, outgoing proposals, one-tap accept/decline
5. **Credits Wallet** — Balance, earned/spent history, transaction list
6. **My Listings** — Active, pending, completed trades

**ND-specific UI:**
- Large condition badges with icon + text
- Fixed message templates (tap to select, editable if needed)
- "No negotiation" toggle on listings
- Step indicators: "Step 1 → Step 2 → Step 3"
- No "is typing" indicators
- Explicit pickup/shipping choice with scheduled times

---

## Phase 2: Revenue & Scale (3–6 months)

### Task 11: Shipping Label Integration

- Partner with Pirate Ship API or EasyPost
- User buys discounted label in-app
- Platform takes $0.50–$1 cut
- Tracking integration
- Only for trades where both parties opt-in to shipping

### Task 12: Advanced Moderation

- Auto-split groups at 1,000 members
- Distributed moderation (trusted users get mod privileges)
- Automated flagging (keyword detection, repeat complainers)
- Community guidelines enforcement

### Task 13: Nonprofit Partnerships

- Pass It On Center integration (national disability equipment network)
- State-specific programs: TechOWL (PA), REquipment (MA), CReATE (UT)
- Equipment safety recall database integration
- Insurance coordination documentation

### Task 14: Tax Compliance

- 1099-B equivalent generation for users with >$600 in trade value
- Trade value tracking dashboard
- Terms of service update
- Legal review of credit system classification

---

## Key Metrics (From Day One)

| Metric | Month 1 Target | Month 3 Target | Month 6 Target |
|--------|---------------|---------------|---------------|
| Trade completion rate | >20% | >30% | >40% |
| ND user satisfaction | >3.8/5 | >4.0/5 | >4.2/5 |
| Dispute rate | <8% | <5% | <3% |
| Avg time to complete trade | <10 days | <7 days | <5 days |
| Verified trader adoption | N/A | >5% | >15% |
| Multi-party matches found | Track | >5/week | >20/week |

---

## Files Summary

**Backend:**
- `server/app/models/trade.py` — Credit ledger
- `server/app/schemas/trade.py` — Pydantic models
- `server/app/services/trade_service.py` — Core trade logic
- `server/app/services/trade_templates.py` — ND-friendly templates
- `server/app/services/trade_matcher.py` — Algorithmic matching
- `server/app/services/safety_checklists.py` — Category-specific safety
- `server/app/api/routes/trade.py` — API routes

**Frontend:**
- `app/lib/features/trade/screens/*` — 6 trade screens
- `app/lib/features/trade/widgets/*` — Reusable widgets
- `app/lib/features/trade/models/trade_models.dart` — Data models

**Tests:**
- `server/tests/test_trade_credits.py`
- `server/tests/test_trade_listings.py`
- `server/tests/test_trade_service.py`
- `server/tests/test_trade_api.py`
- `server/tests/test_trade_nd_ux.py`
- `server/tests/test_trade_reputation.py`
- `server/tests/test_trade_safety.py`
- `server/tests/test_trade_verified.py`
- `server/tests/test_trade_matcher.py`
