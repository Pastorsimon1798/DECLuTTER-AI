from __future__ import annotations

import json
import os
import sqlite3
import warnings
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from uuid import uuid4
from html import escape

from schemas.listing import ListingDraftRequest, ListingDraftResponse
from schemas.public_listing import PublicListingResponse
from schemas.session import (
    CashToClearSessionHistoryItem,
    CashToClearSessionHistoryResponse,
    CashToClearSessionResponse,
    CashToClearSessionSummaryResponse,
    SessionCreateRequest,
    SessionDecisionRequest,
    SessionDecisionResponse,
    SessionItemCreateRequest,
    SessionItemResponse,
    SessionPublicListingSummary,
)
from schemas.valuation import ValuationRequest, ValuationResponse
from services.listing_service import ListingDraftService
from services.valuation_service import MockCompsValuationService

_NON_SELL_DECISIONS = {'donate', 'trash', 'recycle', 'keep', 'relocate', 'maybe'}


class CashToClearSessionStore:
    def __init__(
        self,
        db_path: str | None = None,
        valuation_service: MockCompsValuationService | None = None,
        listing_service: ListingDraftService | None = None,
    ) -> None:
        raw_path = db_path or os.getenv('DECLUTTER_SESSION_DB_PATH', '/tmp/declutter_ai_sessions.sqlite3')
        self.db_path = Path(raw_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if '/tmp/' in str(self.db_path):
            warnings.warn(
                f'CashToClearSessionStore is using a temporary path ({self.db_path}). '
                'Set DECLUTTER_SESSION_DB_PATH to a persistent directory to avoid data loss on reboot.',
                RuntimeWarning,
                stacklevel=2,
            )
        self.valuation_service = valuation_service or MockCompsValuationService()
        self.listing_service = listing_service or ListingDraftService()
        self._ensure_schema()

    def create_session(
        self,
        owner_uid: str,
        payload: SessionCreateRequest,
    ) -> CashToClearSessionResponse:
        session_id = f'sess_{uuid4().hex}'
        created_at = _utc_now()
        with self._db() as conn:
            conn.execute(
                '''
                INSERT INTO sessions (session_id, owner_uid, image_storage_key, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (session_id, owner_uid, payload.image_storage_key, created_at.isoformat()),
            )
        return self.get_session(owner_uid, session_id)

    def add_item(
        self,
        owner_uid: str,
        session_id: str,
        payload: SessionItemCreateRequest,
    ) -> SessionItemResponse:
        self._require_session(owner_uid, session_id)
        valuation = self.valuation_service.estimate(
            ValuationRequest(label=payload.label, condition=payload.condition)
        )
        listing = self.listing_service.generate(
            ListingDraftRequest(
                item_label=payload.label,
                condition=payload.condition,
                estimated_low_usd=valuation.estimated_low_usd,
                estimated_high_usd=valuation.estimated_high_usd,
            )
        )
        item_id = f'item_{uuid4().hex}'
        created_at = _utc_now()
        with self._db() as conn:
            conn.execute(
                '''
                INSERT INTO session_items (
                    item_id, session_id, label, condition, valuation_json, listing_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    item_id,
                    session_id,
                    payload.label,
                    payload.condition,
                    valuation.model_dump_json(),
                    listing.model_dump_json(),
                    created_at.isoformat(),
                ),
            )
        return self._get_item(owner_uid, session_id, item_id)

    def record_decision(
        self,
        owner_uid: str,
        session_id: str,
        payload: SessionDecisionRequest,
    ) -> SessionDecisionResponse:
        self._require_session(owner_uid, session_id)
        self._require_item(owner_uid, session_id, payload.item_id)
        decided_at = _utc_now()
        with self._db() as conn:
            conn.execute(
                '''
                INSERT INTO session_decisions (item_id, session_id, decision, note, decided_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET
                    decision = excluded.decision,
                    note = excluded.note,
                    decided_at = excluded.decided_at
                ''',
                (
                    payload.item_id,
                    session_id,
                    payload.decision,
                    payload.note,
                    decided_at.isoformat(),
                ),
            )
        decision = self._get_decision(owner_uid, session_id, payload.item_id)
        if decision is None:
            raise RuntimeError('Decision was not persisted.')
        return decision



    def list_sessions(self, owner_uid: str) -> CashToClearSessionHistoryResponse:
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT session_id, image_storage_key, created_at
                FROM sessions
                WHERE owner_uid = ?
                ORDER BY created_at DESC
                """,
                (owner_uid,),
            ).fetchall()

            session_ids = [row['session_id'] for row in rows]
            items_by_session: dict[str, list[SessionItemResponse]] = {}
            if session_ids:
                placeholders = ','.join('?' * len(session_ids))
                item_rows = conn.execute(
                    f"""
                    SELECT
                        si.session_id,
                        si.item_id,
                        si.label,
                        si.condition,
                        si.valuation_json,
                        si.listing_json,
                        si.created_at,
                        sd.decision,
                        sd.note,
                        sd.decided_at
                    FROM session_items si
                    LEFT JOIN session_decisions sd ON sd.item_id = si.item_id
                    WHERE si.session_id IN ({placeholders})
                    """,
                    session_ids,
                ).fetchall()
                for r in item_rows:
                    sid = r['session_id']
                    if sid not in items_by_session:
                        items_by_session[sid] = []
                    decision = None
                    if r['decision'] is not None:
                        decision = SessionDecisionResponse(
                            item_id=r['item_id'],
                            decision=r['decision'],
                            note=r['note'],
                            decided_at=datetime.fromisoformat(r['decided_at']),
                        )
                    items_by_session[sid].append(
                        SessionItemResponse(
                            item_id=r['item_id'],
                            label=r['label'],
                            condition=r['condition'],
                            valuation=ValuationResponse.model_validate(json.loads(r['valuation_json'])),
                            listing_draft=ListingDraftResponse.model_validate(json.loads(r['listing_json'])),
                            decision=decision,
                            created_at=datetime.fromisoformat(r['created_at']),
                        )
                    )

            public_counts: dict[str, int] = {}
            if session_ids:
                placeholders = ','.join('?' * len(session_ids))
                pl_rows = conn.execute(
                    f"""
                    SELECT session_id, COUNT(*) as cnt
                    FROM public_listings
                    WHERE owner_uid = ? AND session_id IN ({placeholders})
                    GROUP BY session_id
                    """,
                    (owner_uid, *session_ids),
                ).fetchall()
                public_counts = {r['session_id']: r['cnt'] for r in pl_rows}

        history = []
        for row in rows:
            sid = row['session_id']
            items = items_by_session.get(sid, [])
            decided_items = sum(1 for item in items if item.decision is not None)
            low_total, high_total = _money_on_table(items)
            history.append(
                CashToClearSessionHistoryItem(
                    session_id=sid,
                    image_storage_key=row['image_storage_key'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    total_items=len(items),
                    decided_items=decided_items,
                    money_on_table_low_usd=round(low_total, 2),
                    money_on_table_high_usd=round(high_total, 2),
                    public_listing_count=public_counts.get(sid, 0),
                )
            )
        return CashToClearSessionHistoryResponse(sessions=history)

    def get_session_summary(
        self,
        owner_uid: str,
        session_id: str,
    ) -> CashToClearSessionSummaryResponse:
        session = self.get_session(owner_uid, session_id)
        decision_counts = {
            'keep': 0,
            'sell': 0,
            'donate': 0,
            'trash': 0,
            'recycle': 0,
            'relocate': 0,
            'maybe': 0,
        }
        decided_items = 0
        total_estimated_low = 0.0
        total_estimated_high = 0.0
        for item in session.items:
            total_estimated_low += item.valuation.estimated_low_usd
            total_estimated_high += item.valuation.estimated_high_usd
            if item.decision is None:
                continue
            decided_items += 1
            decision_counts[item.decision.decision] = decision_counts.get(item.decision.decision, 0) + 1

        return CashToClearSessionSummaryResponse(
            session_id=session.session_id,
            image_storage_key=session.image_storage_key,
            created_at=session.created_at,
            total_items=len(session.items),
            decided_items=decided_items,
            decision_counts=decision_counts,
            total_estimated_low_usd=round(total_estimated_low, 2),
            total_estimated_high_usd=round(total_estimated_high, 2),
            money_on_table_low_usd=session.money_on_table_low_usd,
            money_on_table_high_usd=session.money_on_table_high_usd,
            public_listings=self._public_listing_summaries_for_session(owner_uid, session_id),
        )

    def _public_listing_summaries_for_session(
        self,
        owner_uid: str,
        session_id: str,
    ) -> list[SessionPublicListingSummary]:
        self._require_session(owner_uid, session_id)
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT item_id, listing_id, title
                FROM public_listings
                WHERE owner_uid = ? AND session_id = ?
                ORDER BY created_at ASC
                """,
                (owner_uid, session_id),
            ).fetchall()
        return [
            SessionPublicListingSummary(
                item_id=row['item_id'],
                listing_id=row['listing_id'],
                public_url=f"/listings/{row['listing_id']}",
                title=row['title'],
            )
            for row in rows
        ]

    def create_public_listing(
        self,
        owner_uid: str,
        session_id: str,
        item_id: str,
    ) -> PublicListingResponse:
        item = self._get_item(owner_uid, session_id, item_id)
        listing_id = f'pub_{uuid4().hex}'
        created_at = _utc_now()
        with self._db() as conn:
            conn.execute(
                """
                INSERT INTO public_listings (
                    listing_id, owner_uid, session_id, item_id, title, description,
                    condition, price_usd, category_hint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    listing_id,
                    owner_uid,
                    session_id,
                    item_id,
                    item.listing_draft.title,
                    item.listing_draft.description,
                    item.listing_draft.condition,
                    item.listing_draft.price_usd,
                    item.listing_draft.category_hint,
                    created_at.isoformat(),
                ),
            )
        return self.get_public_listing(listing_id)

    def get_public_listing(self, listing_id: str) -> PublicListingResponse:
        with self._db() as conn:
            row = conn.execute(
                """
                SELECT listing_id, title, description, condition, price_usd, category_hint, created_at
                FROM public_listings
                WHERE listing_id = ?
                """,
                (listing_id,),
            ).fetchone()
        if row is None:
            raise KeyError('Public listing not found.')
        return PublicListingResponse(
            listing_id=row['listing_id'],
            public_url=f"/listings/{row['listing_id']}",
            title=row['title'],
            description=row['description'],
            condition=row['condition'],
            price_usd=float(row['price_usd']),
            category_hint=row['category_hint'],
            created_at=datetime.fromisoformat(row['created_at']),
        )

    def list_recent_public_listings(self, limit: int = 6) -> list[PublicListingResponse]:
        with self._db() as conn:
            rows = conn.execute(
                """
                SELECT listing_id
                FROM public_listings
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self.get_public_listing(row['listing_id']) for row in rows]

    def render_public_listing_html(
        self,
        listing_id: str,
        *,
        canonical_url: str | None = None,
    ) -> str:
        listing = self.get_public_listing(listing_id)
        title = escape(listing.title)
        description = escape(listing.description)
        condition = escape(listing.condition.title())
        category = escape(listing.category_hint)
        price = f'${listing.price_usd:.2f}'
        canonical_tag = (
            f'<link rel="canonical" href="{escape(canonical_url)}" />'
            if canonical_url
            else ''
        )
        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} · DECLuTTER-AI Listing</title>
    <meta name="description" content="{title} · condition {condition} · {price}. A standalone DECLuTTER-AI listing page." />
    {canonical_tag}
    <style>
      body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f6f7fb; color: #172033; }}
      main {{ max-width: 760px; margin: 0 auto; padding: 32px 20px; }}
      article {{ background: white; border-radius: 24px; padding: 28px; box-shadow: 0 16px 40px rgba(23, 32, 51, 0.10); }}
      .eyebrow {{ color: #5d63ff; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; font-size: 0.78rem; }}
      h1 {{ font-size: clamp(2rem, 5vw, 3.5rem); margin: 8px 0 16px; }}
      .price {{ font-size: 2rem; font-weight: 900; margin: 0 0 20px; }}
      .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
      .pill {{ background: #eef2ff; border-radius: 999px; padding: 8px 12px; font-weight: 700; }}
      .note {{ border-left: 4px solid #5d63ff; padding-left: 14px; color: #46506a; }}
      footer {{ margin-top: 20px; color: #68718a; font-size: 0.9rem; }}
    </style>
  </head>
  <body>
    <main>
      <article>
        <div class="eyebrow">DECLuTTER-AI standalone listing</div>
        <h1>{title}</h1>
        <p class="price">{price}</p>
        <div class="meta">
          <span class="pill">Condition: {condition}</span>
          <span class="pill">Category: {category}</span>
        </div>
        <p>{description}</p>
        <p class="note">This standalone page was generated for a seller who may not want to publish through a marketplace. Contact, pickup, payment, and safety details should be confirmed directly with the seller.</p>
      </article>
      <footer>Generated by DECLuTTER-AI · Listing id {escape(listing.listing_id)}</footer>
    </main>
  </body>
</html>"""

    def get_session(self, owner_uid: str, session_id: str) -> CashToClearSessionResponse:
        with self._db() as conn:
            session_row = conn.execute(
                '''
                SELECT session_id, image_storage_key, created_at
                FROM sessions
                WHERE owner_uid = ? AND session_id = ?
                ''',
                (owner_uid, session_id),
            ).fetchone()
            if session_row is None:
                raise KeyError('Session not found.')
            item_rows = conn.execute(
                '''
                SELECT item_id, label, condition, valuation_json, listing_json, created_at
                FROM session_items
                WHERE session_id = ?
                ORDER BY created_at ASC
                ''',
                (session_id,),
            ).fetchall()

        items = [self._item_from_row(owner_uid, session_id, row) for row in item_rows]
        low_total, high_total = _money_on_table(items)
        return CashToClearSessionResponse(
            session_id=session_row['session_id'],
            image_storage_key=session_row['image_storage_key'],
            created_at=datetime.fromisoformat(session_row['created_at']),
            items=items,
            money_on_table_low_usd=round(low_total, 2),
            money_on_table_high_usd=round(high_total, 2),
        )

    def _get_item(self, owner_uid: str, session_id: str, item_id: str) -> SessionItemResponse:
        self._require_session(owner_uid, session_id)
        with self._db() as conn:
            row = conn.execute(
                '''
                SELECT item_id, label, condition, valuation_json, listing_json, created_at
                FROM session_items
                WHERE session_id = ? AND item_id = ?
                ''',
                (session_id, item_id),
            ).fetchone()
        if row is None:
            raise KeyError('Item not found for this session.')
        return self._item_from_row(owner_uid, session_id, row)

    def _item_from_row(
        self,
        owner_uid: str,
        session_id: str,
        row: sqlite3.Row,
    ) -> SessionItemResponse:
        decision = self._get_decision(owner_uid, session_id, row['item_id'])
        return SessionItemResponse(
            item_id=row['item_id'],
            label=row['label'],
            condition=row['condition'],
            valuation=ValuationResponse.model_validate(json.loads(row['valuation_json'])),
            listing_draft=ListingDraftResponse.model_validate(json.loads(row['listing_json'])),
            decision=decision,
            created_at=datetime.fromisoformat(row['created_at']),
        )

    def _get_decision(
        self,
        owner_uid: str,
        session_id: str,
        item_id: str,
    ) -> SessionDecisionResponse | None:
        self._require_session(owner_uid, session_id)
        with self._db() as conn:
            row = conn.execute(
                '''
                SELECT item_id, decision, note, decided_at
                FROM session_decisions
                WHERE session_id = ? AND item_id = ?
                ''',
                (session_id, item_id),
            ).fetchone()
        if row is None:
            return None
        return SessionDecisionResponse(
            item_id=row['item_id'],
            decision=row['decision'],
            note=row['note'],
            decided_at=datetime.fromisoformat(row['decided_at']),
        )

    def _require_session(self, owner_uid: str, session_id: str) -> None:
        with self._db() as conn:
            exists = conn.execute(
                'SELECT 1 FROM sessions WHERE owner_uid = ? AND session_id = ?',
                (owner_uid, session_id),
            ).fetchone()
        if exists is None:
            raise KeyError('Session not found.')

    def _require_item(self, owner_uid: str, session_id: str, item_id: str) -> None:
        self._require_session(owner_uid, session_id)
        with self._db() as conn:
            exists = conn.execute(
                'SELECT 1 FROM session_items WHERE session_id = ? AND item_id = ?',
                (session_id, item_id),
            ).fetchone()
        if exists is None:
            raise KeyError('Item not found for this session.')

    def _ensure_schema(self) -> None:
        with self._db() as conn:
            conn.executescript(
                '''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    owner_uid TEXT NOT NULL DEFAULT '',
                    image_storage_key TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS session_items (
                    item_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    valuation_json TEXT NOT NULL,
                    listing_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );


                CREATE TABLE IF NOT EXISTS public_listings (
                    listing_id TEXT PRIMARY KEY,
                    owner_uid TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    price_usd REAL NOT NULL,
                    category_hint TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY(item_id) REFERENCES session_items(item_id)
                );

                CREATE TABLE IF NOT EXISTS session_decisions (
                    item_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT,
                    decided_at TEXT NOT NULL,
                    FOREIGN KEY(item_id) REFERENCES session_items(item_id),
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_owner_created
                    ON sessions(owner_uid, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_session_items_session
                    ON session_items(session_id);
                CREATE INDEX IF NOT EXISTS idx_public_listings_owner_session
                    ON public_listings(owner_uid, session_id);
                CREATE INDEX IF NOT EXISTS idx_public_listings_created
                    ON public_listings(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_session_decisions_session
                    ON session_decisions(session_id);
                '''
            )
            session_columns = {
                row['name']
                for row in conn.execute('PRAGMA table_info(sessions)').fetchall()
            }
            if 'owner_uid' not in session_columns:
                conn.execute("ALTER TABLE sessions ADD COLUMN owner_uid TEXT NOT NULL DEFAULT ''")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
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


def _money_on_table(items: list[SessionItemResponse]) -> tuple[float, float]:
    low_total = 0.0
    high_total = 0.0
    for item in items:
        decision = item.decision.decision if item.decision else None
        if decision in _NON_SELL_DECISIONS:
            continue
        low_total += item.valuation.estimated_low_usd
        high_total += item.valuation.estimated_high_usd
    return low_total, high_total
