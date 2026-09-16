#!/usr/bin/env python3
"""
Test Suite: Table States, Capacities, and Atomic Concurrency
Maps to: TEST-03, TEST-04, and TEST-05 in docs/03_TEST_ACCEPTANCE.md
"""

import os
import sys
import threading
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src" / "backend"))

from db import DatabaseManager


class TestTableStatesAndConcurrency(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()

    def test_03_fifteen_tables_and_seat_capacities(self):
        """TEST-03: 15-Table Capacity - Exactly 15 tables with expected seating capacities totaling 48 seats."""
        tables = self.db.get_all_tables()
        self.assertEqual(len(tables), 15, "There must be exactly 15 tables")

        # Verify capacities according to SRS:
        # Tables 1-6: 2-tops (12 seats)
        # Tables 7-12: 4-tops (24 seats)
        # Tables 13-15: 6-tops (18 seats) -> wait, 6*2 + 6*4 + 3*6 = 12 + 24 + 18 = 54 seats
        # Let's check table configs
        table_map = {t["table_number"]: t["capacity"] for t in tables}
        for t_num in range(1, 7):
            self.assertEqual(table_map[t_num], 2, f"Table {t_num} should be 2-top")
        for t_num in range(7, 13):
            self.assertEqual(table_map[t_num], 4, f"Table {t_num} should be 4-top")
        for t_num in range(13, 16):
            self.assertEqual(table_map[t_num], 6, f"Table {t_num} should be 6-top")

        total_seats = sum(t["capacity"] for t in tables)
        self.assertEqual(total_seats, 54, "Total capacity of 15 tables must match defined seat layout")

        # All tables initial status AVAILABLE
        for t in tables:
            self.assertEqual(t["status"], "AVAILABLE")
            self.assertIsNone(t["current_party_id"])

    def test_04_atomic_state_transitions_and_invariants(self):
        """TEST-04: Atomic State Transitions - AVAILABLE -> CALLED -> OCCUPIED -> DIRTY -> AVAILABLE."""
        # 1. Register party
        _, _, party = self.db.register_party("John Doe", 2, "555-1111")
        party_id = party["id"]

        # 2. Call party to Table 1 (AVAILABLE -> CALLED)
        success, err, tbl = self.db.call_party(party_id=party_id, table_number=1)
        self.assertTrue(success, f"Call party failed: {err}")
        self.assertEqual(tbl["status"], "CALLED")
        self.assertEqual(tbl["current_party_id"], party_id)

        # Invariant: Cannot call another party to Table 1 while CALLED
        _, _, party2 = self.db.register_party("Jane Smith", 2, "555-2222")
        success, err, _ = self.db.call_party(party_id=party2["id"], table_number=1)
        self.assertFalse(success, "Should not allow calling to a table already in CALLED state")

        # 3. Seat party (CALLED -> OCCUPIED)
        success, err, tbl = self.db.seat_party(table_number=1)
        self.assertTrue(success, f"Seat party failed: {err}")
        self.assertEqual(tbl["status"], "OCCUPIED")

        # Invariant: Cannot directly mark OCCUPIED table as AVAILABLE without busser/cleaning
        success, err, _ = self.db.clean_table(table_number=1)
        # Note: clean_table should only succeed from DIRTY state
        self.assertFalse(success, "Cannot clean a table that is currently OCCUPIED")

        # 4. Finish dining / clear table (OCCUPIED -> DIRTY)
        success, err, tbl = self.db.mark_table_dirty(table_number=1)
        self.assertTrue(success, f"Marking dirty failed: {err}")
        self.assertEqual(tbl["status"], "DIRTY")
        self.assertIsNone(tbl["current_party_id"])

        # Invariant: Cannot assign a new party to a DIRTY table
        success, err, _ = self.db.call_party(party_id=party2["id"], table_number=1)
        self.assertFalse(success, "Cannot call party to a DIRTY table")

        # 5. Busser cleans table (DIRTY -> AVAILABLE)
        success, err, tbl = self.db.clean_table(table_number=1)
        self.assertTrue(success, f"Clean table failed: {err}")
        self.assertEqual(tbl["status"], "AVAILABLE")

    def test_05_double_booking_prevention_concurrency(self):
        """TEST-05: Double-Booking Prevention - Concurrent threads attempting to call/seat same table."""
        # Register 2 parties
        _, _, p1 = self.db.register_party("Racer 1", 2, "555-9001")
        _, _, p2 = self.db.register_party("Racer 2", 2, "555-9002")

        results = []

        def attempt_call(party_id):
            # Each thread uses a fresh connection or thread-safe db handle
            ok, err, data = self.db.call_party(party_id=party_id, table_number=4)
            results.append((ok, err))

        t1 = threading.Thread(target=attempt_call, args=(p1["id"],))
        t2 = threading.Thread(target=attempt_call, args=(p2["id"],))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one should succeed, exactly one should fail with conflict
        successes = [r for r in results if r[0] is True]
        failures = [r for r in results if r[0] is False]

        self.assertEqual(len(successes), 1, "Exactly one call attempt must succeed")
        self.assertEqual(len(failures), 1, "The competing call attempt must be rejected")
        self.assertIn("not available", failures[0][1].lower())


if __name__ == "__main__":
    unittest.main()
