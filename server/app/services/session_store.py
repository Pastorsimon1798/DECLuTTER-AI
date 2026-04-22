from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from schemas.listing import ListingDraftRequest, ListingDraftResponse
from schemas.session import (
    CashToClearSessionResponse,
    SessionCreateRequest,
    SessionDecisionRequest,
    SessionDecisionResponse,
    SessionItemCreateRequest,
    SessionItemResponse,
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
        self.db_path = Path(
            db_path or os.getenv('DECLUTTER_SESSION_DB_PATH', '/tmp/declutter_ai_sessions.sqlite3')
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
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
        with self._connect() as conn:
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
        with self._connect() as conn:
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
        with self._connect() as conn:
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

    def get_session(self, owner_uid: str, session_id: str) -> CashToClearSessionResponse:
        with self._connect() as conn:
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
        with self._connect() as conn:
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
        with self._connect() as conn:
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
        with self._connect() as conn:
            exists = conn.execute(
                'SELECT 1 FROM sessions WHERE owner_uid = ? AND session_id = ?',
                (owner_uid, session_id),
            ).fetchone()
        if exists is None:
            raise KeyError('Session not found.')

    def _require_item(self, owner_uid: str, session_id: str, item_id: str) -> None:
        self._require_session(owner_uid, session_id)
        with self._connect() as conn:
            exists = conn.execute(
                'SELECT 1 FROM session_items WHERE session_id = ? AND item_id = ?',
                (session_id, item_id),
            ).fetchone()
        if exists is None:
            raise KeyError('Item not found for this session.')

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
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

                CREATE TABLE IF NOT EXISTS session_decisions (
                    item_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    note TEXT,
                    decided_at TEXT NOT NULL,
                    FOREIGN KEY(item_id) REFERENCES session_items(item_id),
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
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
