#!/usr/bin/env python3
"""
Database Management & Persistence Engine for 15-Table Restaurant Waitlist.
Supports PostgreSQL (production) and SQLite WAL (local testing & zero-setup dev)
with atomic transactional row-level consistency.
"""

import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        # Normalize trailing Z
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)
    except Exception:
        return None


class DatabaseManager:
    def __init__(self, db_path_or_url: Optional[str] = None):
        self.raw_target = db_path_or_url or os.environ.get("DATABASE_URL", "restaurant.db")
        self._lock = threading.RLock()
        self.is_postgres = self.raw_target.startswith("postgres://") or self.raw_target.startswith("postgresql://")

        if self.is_postgres:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.conn = psycopg2.connect(self.raw_target, cursor_factory=RealDictCursor)
            self.conn.autocommit = False
        else:
            self.db_path = self.raw_target
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            if self.db_path != ":memory:":
                self.conn.execute("PRAGMA journal_mode=WAL;")
                self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA foreign_keys=ON;")

    def initialize_schema(self) -> None:
        with self._lock:
            cur = self.conn.cursor()
            if self.is_postgres:
                schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
                if os.path.exists(schema_path):
                    with open(schema_path, "r", encoding="utf-8") as f:
                        cur.execute(f.read())
                    self.conn.commit()
            else:
                # SQLite Schema
                cur.execute("""
                CREATE TABLE IF NOT EXISTS tables (
                    table_number INTEGER PRIMARY KEY,
                    capacity INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'AVAILABLE',
                    current_party_id INTEGER NULL,
                    seated_at TEXT NULL,
                    updated_at TEXT NOT NULL
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS queue_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_uuid TEXT UNIQUE NOT NULL,
                    guest_name TEXT NOT NULL,
                    party_size INTEGER NOT NULL,
                    phone_number TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'WAITING',
                    assigned_table_number INTEGER NULL,
                    joined_at TEXT NOT NULL,
                    called_at TEXT NULL,
                    reminder_sent_at TEXT NULL,
                    seated_at TEXT NULL,
                    completed_at TEXT NULL,
                    FOREIGN KEY (assigned_table_number) REFERENCES tables (table_number)
                );
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS queue_audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    ticket_id INTEGER NULL,
                    table_number INTEGER NULL,
                    payload TEXT NULL,
                    created_at TEXT NOT NULL
                );
                """)

                # Seed 15 tables with capacities
                # Tables 1-6: 2-tops (12 seats)
                # Tables 7-12: 4-tops (24 seats)
                # Tables 13-15: 6-tops (18 seats) => Total 54 seats
                current_time = now_utc().isoformat()
                for t in range(1, 16):
                    cap = 2 if t <= 6 else (4 if t <= 12 else 6)
                    cur.execute("""
                    INSERT OR IGNORE INTO tables (table_number, capacity, status, updated_at)
                    VALUES (?, ?, 'AVAILABLE', ?)
                    """, (t, cap, current_time))

                self.conn.commit()

    def register_party(self, guest_name: str, party_size: int, phone_number: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        if not guest_name or not guest_name.strip():
            return False, "Guest name cannot be blank.", None
        guest_name = guest_name.strip()

        try:
            party_size = int(party_size)
        except (ValueError, TypeError):
            return False, "Party size must be a valid integer.", None

        if party_size < 1 or party_size > 20:
            return False, "Party size must be between 1 and 20 guests.", None

        if not phone_number or not phone_number.strip():
            return False, "Phone number cannot be blank.", None
        phone_number = phone_number.strip()

        ticket_uuid = uuid.uuid4().hex[:12]
        joined_at = now_utc().isoformat()

        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("""
                INSERT INTO queue_entries (ticket_uuid, guest_name, party_size, phone_number, status, joined_at)
                VALUES (?, ?, ?, ?, 'WAITING', ?)
                """, (ticket_uuid, guest_name, party_size, phone_number, joined_at))
                party_id = cur.lastrowid

                # Audit event
                cur.execute("""
                INSERT INTO queue_audit_events (event_type, ticket_id, created_at)
                VALUES ('GUEST_JOINED', ?, ?)
                """, (party_id, joined_at))

                self.conn.commit()

                data = {
                    "id": party_id,
                    "ticket_uuid": ticket_uuid,
                    "guest_name": guest_name,
                    "party_size": party_size,
                    "phone_number": phone_number,
                    "status": "WAITING",
                    "joined_at": joined_at
                }
                return True, None, data
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def get_active_queue(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
            SELECT id, ticket_uuid, guest_name, party_size, phone_number, status, assigned_table_number, joined_at, called_at, reminder_sent_at
            FROM queue_entries
            WHERE status IN ('WAITING', 'CALLED')
            ORDER BY id ASC
            """)
            rows = cur.fetchall()
            result = []
            pos = 1
            for r in rows:
                item = dict(r)
                item["queue_position"] = pos
                pos += 1
                result.append(item)
            return result

    def get_party_status(self, ticket_uuid: str, current_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        now = current_time or now_utc()
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
            SELECT id, ticket_uuid, guest_name, party_size, phone_number, status, assigned_table_number, joined_at, called_at, reminder_sent_at
            FROM queue_entries
            WHERE ticket_uuid = ?
            """, (ticket_uuid,))
            row = cur.fetchone()
            if not row:
                return None

            party = dict(row)

            # Queue position
            if party["status"] == "WAITING":
                cur.execute("""
                SELECT COUNT(*) as pos_ahead
                FROM queue_entries
                WHERE status = 'WAITING' AND id < ?
                """, (party["id"],))
                ahead = cur.fetchone()["pos_ahead"]
                party["queue_position"] = ahead + 1
                # Heuristic: 12 mins per ahead party divided by parallel table turnover
                party["estimated_wait_minutes"] = max(5, (ahead + 1) * 8)
                party["grace_seconds_remaining"] = 0
                party["reminder_due"] = False
                party["expired_hold"] = False
            elif party["status"] == "CALLED":
                party["queue_position"] = 0
                party["estimated_wait_minutes"] = 0
                called_dt = parse_iso(party["called_at"])
                if called_dt:
                    elapsed_seconds = (now - called_dt).total_seconds()
                    party["grace_seconds_remaining"] = max(0, int(600 - elapsed_seconds))
                    # 7-minute reminder due between 420s and 600s if not already sent
                    party["reminder_due"] = (elapsed_seconds >= 420 and elapsed_seconds < 600 and party["reminder_sent_at"] is None)
                    party["expired_hold"] = (elapsed_seconds >= 600)
                else:
                    party["grace_seconds_remaining"] = 600
                    party["reminder_due"] = False
                    party["expired_hold"] = False
            else:
                party["queue_position"] = 0
                party["estimated_wait_minutes"] = 0
                party["grace_seconds_remaining"] = 0
                party["reminder_due"] = False
                party["expired_hold"] = False

            return party

    def record_reminder_sent(self, ticket_uuid: str, sent_at: Optional[datetime] = None) -> bool:
        ts = (sent_at or now_utc()).isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("""
                UPDATE queue_entries
                SET reminder_sent_at = ?
                WHERE ticket_uuid = ?
                """, (ts, ticket_uuid))
                self.conn.commit()
                return True
            except Exception:
                self.conn.rollback()
                return False

    def get_all_tables(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute("""
            SELECT t.table_number, t.capacity, t.status, t.current_party_id, t.seated_at, t.updated_at,
                   q.guest_name, q.party_size, q.called_at, q.ticket_uuid
            FROM tables t
            LEFT JOIN queue_entries q ON t.current_party_id = q.id
            ORDER BY t.table_number ASC
            """)
            rows = cur.fetchall()
            tables = []
            now = now_utc()
            for r in rows:
                tbl = dict(r)
                if tbl["status"] == "OCCUPIED" and tbl["seated_at"]:
                    seated_dt = parse_iso(tbl["seated_at"])
                    if seated_dt:
                        tbl["elapsed_dining_minutes"] = int((now - seated_dt).total_seconds() / 60)
                    else:
                        tbl["elapsed_dining_minutes"] = 0
                elif tbl["status"] == "CALLED" and tbl["called_at"]:
                    called_dt = parse_iso(tbl["called_at"])
                    if called_dt:
                        elapsed_s = (now - called_dt).total_seconds()
                        tbl["grace_seconds_remaining"] = max(0, int(600 - elapsed_s))
                        tbl["is_expired"] = elapsed_s >= 600
                        tbl["reminder_due"] = elapsed_s >= 420 and elapsed_s < 600
                    else:
                        tbl["grace_seconds_remaining"] = 600
                        tbl["is_expired"] = False
                        tbl["reminder_due"] = False
                else:
                    tbl["elapsed_dining_minutes"] = 0
                    tbl["grace_seconds_remaining"] = 0
                    tbl["is_expired"] = False
                    tbl["reminder_due"] = False

                tables.append(tbl)
            return tables

    def call_party(self, party_id: int, table_number: int, called_at: Optional[datetime] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        call_time = (called_at or now_utc()).isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                # 1. Verify table status is AVAILABLE
                cur.execute("SELECT table_number, capacity, status FROM tables WHERE table_number = ?", (table_number,))
                tbl = cur.fetchone()
                if not tbl:
                    return False, f"Table {table_number} does not exist.", None
                if tbl["status"] != "AVAILABLE":
                    return False, f"Table {table_number} is not available (current status: {tbl['status']}).", None

                # 2. Verify party is WAITING
                cur.execute("SELECT id, status, guest_name, party_size FROM queue_entries WHERE id = ?", (party_id,))
                party = cur.fetchone()
                if not party:
                    return False, f"Party {party_id} does not exist.", None
                if party["status"] != "WAITING":
                    return False, f"Party {party_id} is not waiting (current status: {party['status']}).", None

                # 3. Transition table to CALLED
                cur.execute("""
                UPDATE tables
                SET status = 'CALLED', current_party_id = ?, updated_at = ?
                WHERE table_number = ? AND status = 'AVAILABLE'
                """, (party_id, call_time, table_number))

                if cur.rowcount == 0:
                    return False, f"Table {table_number} was modified concurrently.", None

                # 4. Transition party to CALLED
                cur.execute("""
                UPDATE queue_entries
                SET status = 'CALLED', assigned_table_number = ?, called_at = ?
                WHERE id = ?
                """, (table_number, call_time, party_id))

                # 5. Audit
                cur.execute("""
                INSERT INTO queue_audit_events (event_type, ticket_id, table_number, created_at)
                VALUES ('PARTY_CALLED', ?, ?, ?)
                """, (party_id, table_number, call_time))

                self.conn.commit()

                return True, None, {
                    "table_number": table_number,
                    "status": "CALLED",
                    "current_party_id": party_id,
                    "called_at": call_time
                }
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def seat_party(self, table_number: int, seated_at: Optional[datetime] = None) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        seat_time = (seated_at or now_utc()).isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT table_number, status, current_party_id FROM tables WHERE table_number = ?", (table_number,))
                tbl = cur.fetchone()
                if not tbl:
                    return False, f"Table {table_number} does not exist.", None
                if tbl["status"] != "CALLED":
                    return False, f"Table {table_number} must be in CALLED status to seat (current status: {tbl['status']}).", None

                party_id = tbl["current_party_id"]

                # Update table to OCCUPIED
                cur.execute("""
                UPDATE tables
                SET status = 'OCCUPIED', seated_at = ?, updated_at = ?
                WHERE table_number = ?
                """, (seat_time, seat_time, table_number))

                # Update queue entry
                if party_id:
                    cur.execute("""
                    UPDATE queue_entries
                    SET status = 'SEATED', seated_at = ?
                    WHERE id = ?
                    """, (seat_time, party_id))

                # Audit
                cur.execute("""
                INSERT INTO queue_audit_events (event_type, ticket_id, table_number, created_at)
                VALUES ('PARTY_SEATED', ?, ?, ?)
                """, (party_id, table_number, seat_time))

                self.conn.commit()

                return True, None, {
                    "table_number": table_number,
                    "status": "OCCUPIED",
                    "current_party_id": party_id,
                    "seated_at": seat_time
                }
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def mark_table_dirty(self, table_number: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        curr_time = now_utc().isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT table_number, status, current_party_id FROM tables WHERE table_number = ?", (table_number,))
                tbl = cur.fetchone()
                if not tbl:
                    return False, f"Table {table_number} does not exist.", None
                if tbl["status"] != "OCCUPIED":
                    return False, f"Table {table_number} must be OCCUPIED to clear (current status: {tbl['status']}).", None

                party_id = tbl["current_party_id"]

                cur.execute("""
                UPDATE tables
                SET status = 'DIRTY', current_party_id = NULL, seated_at = NULL, updated_at = ?
                WHERE table_number = ?
                """, (curr_time, table_number))

                if party_id:
                    cur.execute("""
                    UPDATE queue_entries
                    SET completed_at = ?
                    WHERE id = ?
                    """, (curr_time, party_id))

                cur.execute("""
                INSERT INTO queue_audit_events (event_type, ticket_id, table_number, created_at)
                VALUES ('TABLE_VACATED_DIRTY', ?, ?, ?)
                """, (party_id, table_number, curr_time))

                self.conn.commit()

                return True, None, {
                    "table_number": table_number,
                    "status": "DIRTY",
                    "current_party_id": None
                }
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def clean_table(self, table_number: int) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        curr_time = now_utc().isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("SELECT table_number, status FROM tables WHERE table_number = ?", (table_number,))
                tbl = cur.fetchone()
                if not tbl:
                    return False, f"Table {table_number} does not exist.", None
                if tbl["status"] != "DIRTY":
                    return False, f"Table {table_number} must be DIRTY to clean (current status: {tbl['status']}).", None

                cur.execute("""
                UPDATE tables
                SET status = 'AVAILABLE', current_party_id = NULL, seated_at = NULL, updated_at = ?
                WHERE table_number = ?
                """, (curr_time, table_number))

                cur.execute("""
                INSERT INTO queue_audit_events (event_type, table_number, created_at)
                VALUES ('TABLE_CLEANED_AVAILABLE', ?, ?)
                """, (table_number, curr_time))

                self.conn.commit()

                return True, None, {
                    "table_number": table_number,
                    "status": "AVAILABLE"
                }
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def bump_expired_party(self, table_number: int, current_time: Optional[datetime] = None, force: bool = False) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        now = current_time or now_utc()
        curr_iso = now.isoformat()
        with self._lock:
            try:
                cur = self.conn.cursor()
                cur.execute("""
                SELECT t.table_number, t.status, t.current_party_id, q.called_at, q.ticket_uuid
                FROM tables t
                LEFT JOIN queue_entries q ON t.current_party_id = q.id
                WHERE t.table_number = ?
                """, (table_number,))
                tbl = cur.fetchone()
                if not tbl:
                    return False, f"Table {table_number} does not exist.", None
                if tbl["status"] != "CALLED":
                    return False, f"Table {table_number} is not in CALLED status.", None

                called_dt = parse_iso(tbl["called_at"])
                if not force and called_dt:
                    elapsed_seconds = (now - called_dt).total_seconds()
                    if elapsed_seconds < 600:
                        return False, f"Grace period active ({int(600 - elapsed_seconds)}s remaining). Cannot bump.", None

                party_id = tbl["current_party_id"]

                # Free table
                cur.execute("""
                UPDATE tables
                SET status = 'AVAILABLE', current_party_id = NULL, updated_at = ?
                WHERE table_number = ?
                """, (curr_iso, table_number))

                # Mark party EXPIRED
                if party_id:
                    cur.execute("""
                    UPDATE queue_entries
                    SET status = 'EXPIRED', completed_at = ?
                    WHERE id = ?
                    """, (curr_iso, party_id))

                cur.execute("""
                INSERT INTO queue_audit_events (event_type, ticket_id, table_number, created_at)
                VALUES ('PARTY_BUMPED_EXPIRED', ?, ?, ?)
                """, (party_id, table_number, curr_iso))

                self.conn.commit()

                return True, None, {
                    "table_number": table_number,
                    "status": "AVAILABLE",
                    "current_party_id": None
                }
            except Exception as e:
                self.conn.rollback()
                return False, str(e), None

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
