#!/usr/bin/env python3
"""
Test Suite: Ingress Validation & Sequential Queue Ordering
Maps to: TEST-01 and TEST-02 in docs/03_TEST_ACCEPTANCE.md
"""

import os
import sys
import unittest
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src" / "backend"))

from db import DatabaseManager


class TestIngressAndQueue(unittest.TestCase):
    def setUp(self):
        # Use an in-memory or isolated temp database for each test run
        self.db = DatabaseManager(":memory:")
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()

    def test_01_ingress_validation_rejects_invalid_inputs(self):
        """TEST-01: Ingress Validation - Rejects party size < 1, > 20, blank name, or invalid phone."""
        # Blank name
        success, err, data = self.db.register_party(guest_name="", party_size=2, phone_number="555-1234")
        self.assertFalse(success)
        self.assertIn("name", err.lower())

        # Whitespace-only name
        success, err, data = self.db.register_party(guest_name="   ", party_size=2, phone_number="555-1234")
        self.assertFalse(success)
        self.assertIn("name", err.lower())

        # Party size < 1
        success, err, data = self.db.register_party(guest_name="Alice", party_size=0, phone_number="555-1234")
        self.assertFalse(success)
        self.assertIn("party size", err.lower())

        # Party size > 20
        success, err, data = self.db.register_party(guest_name="Bob", party_size=21, phone_number="555-1234")
        self.assertFalse(success)
        self.assertIn("party size", err.lower())

        # Blank phone number
        success, err, data = self.db.register_party(guest_name="Charlie", party_size=4, phone_number="")
        self.assertFalse(success)
        self.assertIn("phone", err.lower())

        # Valid party registration
        success, err, data = self.db.register_party(guest_name="Valid Guest", party_size=4, phone_number="+1 555-0199")
        self.assertTrue(success)
        self.assertIsNone(err)
        self.assertIsNotNone(data)
        self.assertEqual(data["guest_name"], "Valid Guest")
        self.assertEqual(data["party_size"], 4)
        self.assertEqual(data["status"], "WAITING")

    def test_02_sequential_ticket_queue_ordering(self):
        """TEST-02: Sequential Ticket Queue - Monotonically increasing queue positions and distinct UUIDs."""
        tickets = []
        for i in range(1, 6):
            success, err, data = self.db.register_party(
                guest_name=f"Guest {i}",
                party_size=(i % 4) + 1,
                phone_number=f"555-000{i}"
            )
            self.assertTrue(success, f"Failed registering party {i}: {err}")
            tickets.append(data)

        # Check unique ticket UUIDs
        uuids = [t["ticket_uuid"] for t in tickets]
        self.assertEqual(len(set(uuids)), 5, "Ticket UUIDs must be unique")

        # Check monotonically increasing IDs / positions
        ids = [t["id"] for t in tickets]
        self.assertEqual(ids, sorted(ids), "Ticket IDs must be monotonically increasing")

        # Inspect queue order
        active_queue = self.db.get_active_queue()
        self.assertEqual(len(active_queue), 5)
        for idx, item in enumerate(active_queue):
            self.assertEqual(item["ticket_uuid"], tickets[idx]["ticket_uuid"])
            self.assertEqual(item["queue_position"], idx + 1)


if __name__ == "__main__":
    unittest.main()
