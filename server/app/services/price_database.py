from __future__ import annotations

import json
import os
import sqlite3
import warnings
from dataclasses import dataclass
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta


@dataclass(frozen=True)
class PriceRange:
    """A researched price range for a specific item label."""

    label: str
    normalized_label: str
    category: str
    low_price: float
    median_price: float
    high_price: float
    comp_count: int
    source: str
    confidence: str
    updated_at: str


class PriceDatabase:
    """Local SQLite-backed price database for offline valuation research.

    Supports seeded data, LLM-estimated fallback values, manual user
    overrides, community sale recording, and price feedback.

    All lookups are local — zero external API calls required.
    """

    _SEED_FILE = Path(__file__).parent.parent / "data" / "price_seed.json"

    # TTL for staleness warnings
    TTL_SEEDED_DAYS = 180      # 6 months — static guide data
    TTL_LLM_ESTIMATE_DAYS = 90  # 3 months — LLM estimates drift
    TTL_MANUAL_DAYS = None      # User override never goes stale

    def __init__(self, db_path: str | None = None) -> None:
        raw_path = db_path or os.getenv(
            "DECLUTTER_PRICE_DB_PATH",
            os.getenv("DECLUTTER_SESSION_DB_PATH", "/tmp/declutter_ai_prices.sqlite3"),
        )
        self.db_path = Path(raw_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if "/tmp/" in str(self.db_path):
            warnings.warn(
                f"PriceDatabase is using a temporary path ({self.db_path}). "
                "Set DECLUTTER_PRICE_DB_PATH to a persistent directory to avoid "
                "data loss on reboot.",
                RuntimeWarning,
                stacklevel=2,
            )
        self._ensure_schema()
        self._seed_if_empty()

    # ------------------------------------------------------------------
    # Public API — lookups
    # ------------------------------------------------------------------

    def get_price_range(self, label: str) -> PriceRange | None:
        """Return the best-matching price range for a label."""
        normalized = self._normalize_label(label)

        # 1. Exact match
        exact = self._fetch_exact(normalized)
        if exact is not None:
            return exact

        # 2. Substring matching with scoring
        best_match: PriceRange | None = None
        best_score: tuple[int, int, float] = (-1, 0, 0.0)

        for row in self._all_rows():
            score: tuple[int, int, float] | None = None
            if normalized == row.normalized_label:
                score = (3, 0, row.median_price)
            elif normalized in row.normalized_label:
                score = (2, -len(row.normalized_label), row.median_price)
            elif row.normalized_label in normalized:
                score = (1, len(row.normalized_label), row.median_price)

            if score is not None and score > best_score:
                best_score = score
                best_match = row

        return best_match

    def get_staleness(self, price_range: PriceRange) -> tuple[int, str]:
        """Return (age_days, stale_warning) for a price range."""
        try:
            updated = datetime.fromisoformat(price_range.updated_at)
        except (ValueError, TypeError):
            return (999, "Price record date unknown — treat as stale.")

        age = (_utc_now() - updated).days
        if age < 0:
            age = 0

        ttl_days = self._ttl_for_source(price_range.source)
        if ttl_days is None:
            return (age, "")

        if age > ttl_days:
            return (
                age,
                f"Price is {age} days old (stale after {ttl_days}). "
                "Consider refreshing or overriding.",
            )
        return (age, "")

    # ------------------------------------------------------------------
    # Public API — mutations
    # ------------------------------------------------------------------

    def record_llm_estimate(
        self,
        label: str,
        low: float,
        median: float,
        high: float,
    ) -> PriceRange:
        """Store an LLM-generated price estimate for future cache hits."""
        return self._upsert(
            label=label,
            low=low,
            median=median,
            high=high,
            source="llm_estimate",
            confidence="low",
        )

    def record_manual_override(
        self,
        label: str,
        price: float,
        user_id: str = "",
    ) -> PriceRange:
        """Store a user-manually-entered price as the canonical range."""
        return self._upsert(
            label=label,
            low=price * 0.8,
            median=price,
            high=price * 1.2,
            source="manual",
            confidence="high",
        )

    def record_feedback(
        self,
        label: str,
        expected_median_usd: float,
        reason: str = "",
        source: str = "user",
    ) -> dict:
        """Record user feedback about a price being too high or low.

        Returns dict with previous price, feedback price, and status.
        """
        normalized = self._normalize_label(label)
        previous = self._fetch_exact(normalized)

        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO price_feedback (
                    label, normalized_label, expected_median_usd,
                    reason, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    label,
                    normalized,
                    expected_median_usd,
                    reason,
                    source,
                    _utc_now().isoformat(),
                ),
            )

        # Auto-adjust if we have enough convergent feedback
        self._maybe_adjust_from_feedback(normalized)

        return {
            "label": label,
            "previous_median_usd": previous.median_price if previous else 0.0,
            "feedback_median_usd": expected_median_usd,
            "status": "recorded",
        }

    def record_sale(
        self,
        label: str,
        sale_price_usd: float,
        condition: str = "unknown",
        platform: str = "",
        notes: str = "",
    ) -> dict:
        """Record an actual sale price for community aggregation.

        When enough sales are recorded, the price range is updated to
        reflect real market data.
        """
        normalized = self._normalize_label(label)

        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO community_sales (
                    label, normalized_label, sale_price_usd,
                    condition, platform, notes, sold_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    label,
                    normalized,
                    sale_price_usd,
                    condition,
                    platform,
                    notes,
                    _utc_now().isoformat(),
                ),
            )

        # Auto-adjust if we have enough sales
        self._maybe_adjust_from_sales(normalized)

        return {
            "label": label,
            "sale_price_usd": sale_price_usd,
            "recorded_at": _utc_now().isoformat(),
        }

    # ------------------------------------------------------------------
    # Public API — analytics / health
    # ------------------------------------------------------------------

    def get_stats(self) -> dict[str, int]:
        """Return coverage stats by source."""
        with self._db() as conn:
            rows = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM price_ranges GROUP BY source"
            ).fetchall()
        return {row["source"]: row["cnt"] for row in rows}

    def get_health(self) -> dict:
        """Return data-quality health report."""
        with self._db() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM price_ranges"
            ).fetchone()[0]

            stale_seeded = conn.execute(
                """
                SELECT COUNT(*) FROM price_ranges
                WHERE source = 'seeded'
                AND datetime(updated_at) < datetime('now', '-180 days')
                """
            ).fetchone()[0]

            stale_llm = conn.execute(
                """
                SELECT COUNT(*) FROM price_ranges
                WHERE source = 'llm_estimate'
                AND datetime(updated_at) < datetime('now', '-90 days')
                """
            ).fetchone()[0]

            feedback_count = conn.execute(
                "SELECT COUNT(*) FROM price_feedback"
            ).fetchone()[0]

            sales_count = conn.execute(
                "SELECT COUNT(*) FROM community_sales"
            ).fetchone()[0]

            community_adjusted = conn.execute(
                """
                SELECT COUNT(*) FROM price_ranges
                WHERE source = 'community'
                """
            ).fetchone()[0]

        return {
            "total_price_records": total,
            "stale_seeded_records": stale_seeded,
            "stale_llm_records": stale_llm,
            "total_feedback_entries": feedback_count,
            "total_recorded_sales": sales_count,
            "community_adjusted_prices": community_adjusted,
            "freshness_score": self._freshness_score(total, stale_seeded + stale_llm),
        }

    def get_price_history(self, label: str, limit: int = 20) -> list[dict]:
        """Return price change history for a label."""
        normalized = self._normalize_label(label)
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT low_price, median_price, high_price, source, changed_at
                FROM price_history
                WHERE normalized_label = ?
                ORDER BY changed_at DESC
                LIMIT ?
                """,
                (normalized, limit),
            ).fetchall()
        return [
            {
                "low": row["low_price"],
                "median": row["median_price"],
                "high": row["high_price"],
                "source": row["source"],
                "changed_at": row["changed_at"],
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        with self._db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_ranges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    normalized_label TEXT NOT NULL UNIQUE,
                    category TEXT,
                    low_price REAL NOT NULL,
                    median_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    comp_count INTEGER DEFAULT 0,
                    source TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_price_ranges_normalized
                ON price_ranges(normalized_label)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    normalized_label TEXT NOT NULL,
                    expected_median_usd REAL NOT NULL,
                    reason TEXT,
                    source TEXT DEFAULT 'user',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_normalized
                ON price_feedback(normalized_label)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS community_sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    normalized_label TEXT NOT NULL,
                    sale_price_usd REAL NOT NULL,
                    condition TEXT,
                    platform TEXT,
                    notes TEXT,
                    sold_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sales_normalized
                ON community_sales(normalized_label)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL,
                    normalized_label TEXT NOT NULL,
                    low_price REAL NOT NULL,
                    median_price REAL NOT NULL,
                    high_price REAL NOT NULL,
                    source TEXT NOT NULL,
                    changed_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_history_normalized
                ON price_history(normalized_label)
                """
            )

    def _seed_if_empty(self) -> None:
        with self._db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM price_ranges"
            ).fetchone()[0]
        if count > 0:
            return

        if not self._SEED_FILE.exists():
            warnings.warn(
                f"Price seed file not found: {self._SEED_FILE}",
                RuntimeWarning,
                stacklevel=2,
            )
            return

        seed_data = json.loads(self._SEED_FILE.read_text(encoding="utf-8"))
        now = _utc_now().isoformat()
        with self._db() as conn:
            for entry in seed_data:
                label = entry["label"]
                conn.execute(
                    """
                    INSERT OR IGNORE INTO price_ranges (
                        label, normalized_label, category,
                        low_price, median_price, high_price,
                        comp_count, source, confidence, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        label,
                        self._normalize_label(label),
                        entry.get("category", ""),
                        entry["low"],
                        entry["median"],
                        entry["high"],
                        0,
                        "seeded",
                        entry.get("confidence", "medium"),
                        now,
                    ),
                )

    def _fetch_exact(self, normalized_label: str) -> PriceRange | None:
        with self._db() as conn:
            row = conn.execute(
                """
                SELECT label, normalized_label, category, low_price, median_price,
                       high_price, comp_count, source, confidence, updated_at
                FROM price_ranges
                WHERE normalized_label = ?
                """,
                (normalized_label,),
            ).fetchone()
        if row is None:
            return None
        return PriceRange(
            label=row["label"],
            normalized_label=row["normalized_label"],
            category=row["category"] or "",
            low_price=row["low_price"],
            median_price=row["median_price"],
            high_price=row["high_price"],
            comp_count=row["comp_count"],
            source=row["source"],
            confidence=row["confidence"],
            updated_at=row["updated_at"],
        )

    def _all_rows(self) -> list[PriceRange]:
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT label, normalized_label, category, low_price, median_price,
                       high_price, comp_count, source, confidence, updated_at
                FROM price_ranges
                ORDER BY length(normalized_label) DESC
                """
            ).fetchall()
        return [
            PriceRange(
                label=r["label"],
                normalized_label=r["normalized_label"],
                category=r["category"] or "",
                low_price=r["low_price"],
                median_price=r["median_price"],
                high_price=r["high_price"],
                comp_count=r["comp_count"],
                source=r["source"],
                confidence=r["confidence"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    def _upsert(
        self,
        label: str,
        low: float,
        median: float,
        high: float,
        source: str,
        confidence: str,
    ) -> PriceRange:
        normalized = self._normalize_label(label)

        # Record history before overwriting
        existing = self._fetch_exact(normalized)
        if existing is not None:
            self._record_history(existing)

        now = _utc_now().isoformat()
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO price_ranges (
                    label, normalized_label, category,
                    low_price, median_price, high_price,
                    comp_count, source, confidence, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(normalized_label) DO UPDATE SET
                    low_price = excluded.low_price,
                    median_price = excluded.median_price,
                    high_price = excluded.high_price,
                    source = excluded.source,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at
                """,
                (label, normalized, "", low, median, high, 0, source, confidence, now),
            )
        result = self._fetch_exact(normalized)
        if result is None:
            raise RuntimeError("Price upsert failed unexpectedly.")
        return result

    def _record_history(self, price_range: PriceRange) -> None:
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO price_history (
                    label, normalized_label, low_price, median_price,
                    high_price, source, changed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    price_range.label,
                    price_range.normalized_label,
                    price_range.low_price,
                    price_range.median_price,
                    price_range.high_price,
                    price_range.source,
                    price_range.updated_at,
                ),
            )

    def _maybe_adjust_from_feedback(self, normalized_label: str) -> None:
        """Auto-adjust price if ≥3 feedback entries converge within 40%."""
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT expected_median_usd, label FROM price_feedback
                WHERE normalized_label = ?
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (normalized_label,),
            ).fetchall()

        if len(rows) < 3:
            return

        medians = [r["expected_median_usd"] for r in rows]
        avg = sum(medians) / len(medians)
        variance = max(medians) - min(medians)
        if avg == 0 or variance / avg > 0.40:  # Too much disagreement
            return

        # Convergent feedback — adjust to community median
        low = avg * 0.7
        high = avg * 1.3
        self._upsert(
            label=rows[0]["label"],
            low=low,
            median=avg,
            high=high,
            source="community",
            confidence="medium",
        )

    def _maybe_adjust_from_sales(self, normalized_label: str) -> None:
        """Auto-adjust price if ≥3 sales recorded in last 180 days."""
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT sale_price_usd FROM community_sales
                WHERE normalized_label = ?
                AND datetime(sold_at) > datetime('now', '-180 days')
                ORDER BY sold_at DESC
                LIMIT 10
                """,
                (normalized_label,),
            ).fetchall()

            if len(rows) < 3:
                return

            prices = sorted(r["sale_price_usd"] for r in rows)
            low = prices[0]
            high = prices[-1]
            median = prices[len(prices) // 2]

            # Need the label to upsert — fetch it
            label_row = conn.execute(
                "SELECT label FROM price_ranges WHERE normalized_label = ?",
                (normalized_label,),
            ).fetchone()

            if label_row is None:
                label_row = conn.execute(
                    "SELECT label FROM price_feedback WHERE normalized_label = ? LIMIT 1",
                    (normalized_label,),
                ).fetchone()

        label = label_row["label"] if label_row else normalized_label

        self._upsert(
            label=label,
            low=low,
            median=median,
            high=high,
            source="community",
            confidence="high",
        )

    def _ttl_for_source(self, source: str) -> int | None:
        mapping = {
            "seeded": self.TTL_SEEDED_DAYS,
            "llm_estimate": self.TTL_LLM_ESTIMATE_DAYS,
            "manual": self.TTL_MANUAL_DAYS,
            "community": self.TTL_LLM_ESTIMATE_DAYS,
        }
        return mapping.get(source, self.TTL_LLM_ESTIMATE_DAYS)

    @staticmethod
    def _freshness_score(total: int, stale: int) -> float:
        if total == 0:
            return 1.0
        return round(1.0 - (stale / total), 2)

    @staticmethod
    def _normalize_label(label: str) -> str:
        return label.lower().strip()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def _db(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
