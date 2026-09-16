#!/usr/bin/env python3
"""
Test Suite: Runtime, Build, Schema Migration & Security Assertions
Maps to: RUN-01, RUN-02, RUN-03, and RUN-04 in docs/03_TEST_ACCEPTANCE.md
"""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src" / "backend"))

from db import DatabaseManager


class TestRuntimeAndSecurity(unittest.TestCase):
    def test_run_01_wasmer_and_docker_configuration_exists(self):
        """RUN-01: Verify wasmer.toml and Dockerfile exist and are syntactically valid."""
        backend_dir = BASE_DIR / "src" / "backend"
        wasmer_file = backend_dir / "wasmer.toml"
        docker_file = backend_dir / "Dockerfile"

        self.assertTrue(wasmer_file.exists(), "wasmer.toml must exist in src/backend/")
        self.assertTrue(docker_file.exists(), "Dockerfile must exist in src/backend/")

        wasmer_content = wasmer_file.read_text(encoding="utf-8")
        self.assertIn("[package]", wasmer_content)
        self.assertIn("name =", wasmer_content)

        docker_content = docker_file.read_text(encoding="utf-8")
        self.assertIn("FROM", docker_content)
        self.assertIn("CMD", docker_content)

    def test_run_02_postgresql_schema_file_validity(self):
        """RUN-02: PostgreSQL Migration - Verify schema.sql defines all required tables and constraints."""
        schema_path = BASE_DIR / "src" / "backend" / "schema.sql"
        self.assertTrue(schema_path.exists(), "schema.sql must exist")

        sql = schema_path.read_text(encoding="utf-8")
        self.assertIn("CREATE TABLE", sql)
        self.assertIn("tables", sql)
        self.assertIn("queue_entries", sql)
        self.assertIn("table_number INT PRIMARY KEY", sql)
        self.assertIn("ticket_uuid", sql)
        self.assertIn("table_status", sql)

    def test_run_03_client_static_bundle_integrity(self):
        """RUN-03: Client Static Bundle - Verify HTML, CSS, and JS assets exist and are linked properly."""
        client_dir = BASE_DIR / "src" / "client"
        index_html = client_dir / "index.html"
        styles_css = client_dir / "styles.css"
        app_js = client_dir / "app.js"

        self.assertTrue(index_html.exists(), "index.html must exist in src/client/")
        self.assertTrue(styles_css.exists(), "styles.css must exist in src/client/")
        self.assertTrue(app_js.exists(), "app.js must exist in src/client/")

        html = index_html.read_text(encoding="utf-8")
        self.assertIn("styles.css", html, "index.html must link to styles.css")
        self.assertIn("app.js", html, "index.html must link to app.js")
        self.assertIn("viewport", html, "index.html must have responsive viewport meta")

    def test_run_04_security_host_pin_authorization(self):
        """RUN-04: Security - Host authorization check requires valid PIN."""
        from app import verify_host_auth

        # Empty PIN
        self.assertFalse(verify_host_auth(""))
        self.assertFalse(verify_host_auth(None))

        # Incorrect PIN
        self.assertFalse(verify_host_auth("wrong-pin"))

        # Default or configured PIN
        self.assertTrue(verify_host_auth("1515"))  # 1515 matches restaurant default host pin


if __name__ == "__main__":
    unittest.main()
