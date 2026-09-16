#!/usr/bin/env python3
"""
Test Suite: 10-Minute Grace Period, 7-Minute Reminder, and Expiry Bump Logic
Maps to: TEST-06 and TEST-07 in docs/03_TEST_ACCEPTANCE.md
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src" / "backend"))

from db import DatabaseManager


class TestGracePeriodAndReminders(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.db.initialize_schema()

    def tearDown(self):
        self.db.close()

    def test_06_grace_period_and_reminder_lifecycle(self):
        """TEST-06: 10-Minute Grace Period & 7-Minute Reminder Logic."""
        # Register a party and call them to Table 3
        _, _, party = self.db.register_party("Late Diner", 4, "555-4444")
        party_id = party["id"]
        ticket_uuid = party["ticket_uuid"]

        # Call party at base_time
        base_time = datetime.now(timezone.utc)
        self.db.call_party(party_id=party_id, table_number=3, called_at=base_time)

        # Check status at minute 0: Grace active, reminder NOT needed yet
        status = self.db.get_party_status(ticket_uuid, current_time=base_time)
        self.assertEqual(status["status"], "CALLED")
        self.assertEqual(status["assigned_table_number"], 3)
        self.assertFalse(status["reminder_due"])
        self.assertFalse(status["expired_hold"])
        self.assertAlmostEqual(status["grace_seconds_remaining"], 600, delta=5)

        # Check status at minute 5: Grace active, reminder NOT needed yet
        t_plus_5m = base_time + timedelta(minutes=5)
        status = self.db.get_party_status(ticket_uuid, current_time=t_plus_5m)
        self.assertEqual(status["status"], "CALLED")
        self.assertFalse(status["reminder_due"])
        self.assertFalse(status["expired_hold"])
        self.assertAlmostEqual(status["grace_seconds_remaining"], 300, delta=5)

        # Check status at minute 7: 2nd Reminder is DUE!
        t_plus_7m = base_time + timedelta(minutes=7, seconds=5)
        status = self.db.get_party_status(ticket_uuid, current_time=t_plus_7m)
        self.assertEqual(status["status"], "CALLED")
        self.assertTrue(status["reminder_due"], "At minute 7, reminder_due must be True")
        self.assertFalse(status["expired_hold"])

        # Mark reminder sent
        self.db.record_reminder_sent(ticket_uuid, sent_at=t_plus_7m)
        status = self.db.get_party_status(ticket_uuid, current_time=t_plus_7m)
        self.assertFalse(status["reminder_due"], "Once recorded sent, reminder_due should be False")

        # Invariant: Before 10 minutes, cannot bump/no-show without manual override flag
        success, err, _ = self.db.bump_expired_party(table_number=3, current_time=t_plus_7m, force=False)
        self.assertFalse(success, "Should not allow normal bump before 10-minute expiry")

        # Check status at minute 10: Grace EXPIRED!
        t_plus_10m = base_time + timedelta(minutes=10, seconds=1)
        status = self.db.get_party_status(ticket_uuid, current_time=t_plus_10m)
        self.assertTrue(status["expired_hold"], "At minute 10, expired_hold must be True")
        self.assertEqual(status["grace_seconds_remaining"], 0)

        # Host executes bump action at minute 10 -> Table becomes AVAILABLE or DIRTY, party becomes EXPIRED
        success, err, bumped_table = self.db.bump_expired_party(table_number=3, current_time=t_plus_10m)
        self.assertTrue(success, f"Bump expired party failed: {err}")
        self.assertEqual(bumped_table["status"], "AVAILABLE")
        self.assertIsNone(bumped_table["current_party_id"])

        # Verify party status is now EXPIRED
        final_party = self.db.get_party_status(ticket_uuid, current_time=t_plus_10m)
        self.assertEqual(final_party["status"], "EXPIRED")

    def test_07_live_tracker_estimated_wait_time_calculation(self):
        """TEST-07: Live Tracker - Estimated wait time based on queue position and table turnover."""
        # Fill queue with 4 parties
        p1 = self.db.register_party("Queue 1", 2, "555-01")[2]
        p2 = self.db.register_party("Queue 2", 2, "555-02")[2]
        p3 = self.db.register_party("Queue 3", 4, "555-03")[2]
        p4 = self.db.register_party("Queue 4", 2, "555-04")[2]

        # Check p4's tracker
        status_p4 = self.db.get_party_status(p4["ticket_uuid"])
        self.assertEqual(status_p4["queue_position"], 4)
        # Position 4 in line should provide reasonable positive estimated wait time
        self.assertGreater(status_p4["estimated_wait_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
