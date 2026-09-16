#!/usr/bin/env python3
"""
High-Performance REST & Server-Sent Events (SSE) HTTP Server
for 15-Table Restaurant Waitlist and Turnover System.
Zero external runtime dependencies; deployable directly to Wasmer or container.
"""

import argparse
import json
import mimetypes
import os
import queue
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
CLIENT_DIR = BASE_DIR / "src" / "client"

sys.path.insert(0, str(BACKEND_DIR))
from db import DatabaseManager

HOST_PIN = os.environ.get("HOST_PIN", "1515")
sse_subscribers: List[queue.Queue] = []
sse_lock = threading.Lock()


def verify_host_auth(pin: Optional[str]) -> bool:
    if not pin:
        return False
    return str(pin).strip() == str(HOST_PIN).strip()


def broadcast_event(event_type: str, data: Any) -> None:
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with sse_lock:
        stale = []
        for q in sse_subscribers:
            try:
                q.put_nowait(message)
            except Exception:
                stale.append(q)
        for s in stale:
            if s in sse_subscribers:
                sse_subscribers.remove(s)


class RestaurantRequestHandler(SimpleHTTPRequestHandler):
    db: DatabaseManager = None  # Injected on server boot

    def send_json_response(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Host-PIN")

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_cors_headers()
        self.end_headers()

    def get_host_pin_from_request(self) -> Optional[str]:
        # Check header first
        pin = self.headers.get("X-Host-PIN")
        if pin:
            return pin
        # Check query string
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if "pin" in qs and qs["pin"]:
            return qs["pin"][0]
        return None

    def read_json_body(self) -> Optional[Dict[str, Any]]:
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            if content_len <= 0:
                return {}
            raw_body = self.rfile.read(content_len).decode("utf-8")
            return json.loads(raw_body)
        except Exception:
            return None

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError):
            pass

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        # Favicon silence
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return


        # SSE Stream Endpoint
        if path == "/api/events":
            self.handle_sse_stream()
            return

        # Public Queue Status Endpoint: /api/queue/<uuid>
        if path.startswith("/api/queue/"):
            ticket_uuid = path.split("/api/queue/")[1].strip("/")
            status_data = self.db.get_party_status(ticket_uuid)
            if not status_data:
                self.send_json_response({"error": "Ticket not found"}, status=404)
                return
            self.send_json_response({"success": True, "ticket": status_data})
            return

        # Host Endpoints
        if path == "/api/host/tables":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            tables = self.db.get_all_tables()
            self.send_json_response({"success": True, "tables": tables})
            return

        if path == "/api/host/queue":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            queue_entries = self.db.get_active_queue()
            self.send_json_response({"success": True, "queue": queue_entries})
            return

        # System Health
        if path == "/api/health":
            self.send_json_response({"status": "healthy", "service": "15-table-waitlist", "tables": 15})
            return

        # Serve static client files if directory exists
        self.serve_static_client(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        if body is None:
            self.send_json_response({"error": "Malformed JSON body"}, status=400)
            return

        # Public Ingress: Register Party
        if path == "/api/queue":
            guest_name = body.get("guest_name", "")
            party_size = body.get("party_size", 0)
            phone_number = body.get("phone_number", "")

            ok, err, data = self.db.register_party(guest_name, party_size, phone_number)
            if not ok:
                self.send_json_response({"error": err}, status=422)
                return

            broadcast_event("QUEUE_UPDATED", {"ticket": data})
            self.send_json_response({"success": True, "ticket": data}, status=201)
            return

        # Host Action: Call Party
        if path == "/api/host/call":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            party_id = body.get("party_id")
            table_number = body.get("table_number")
            if not party_id or not table_number:
                self.send_json_response({"error": "Missing party_id or table_number"}, status=400)
                return

            ok, err, data = self.db.call_party(party_id=int(party_id), table_number=int(table_number))
            if not ok:
                self.send_json_response({"error": err}, status=409)
                return

            broadcast_event("PARTY_CALLED", data)
            broadcast_event("TABLES_UPDATED", self.db.get_all_tables())
            self.send_json_response({"success": True, "data": data})
            return

        # Host Action: Seat Party
        if path == "/api/host/seat":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            table_number = body.get("table_number")
            if not table_number:
                self.send_json_response({"error": "Missing table_number"}, status=400)
                return

            ok, err, data = self.db.seat_party(table_number=int(table_number))
            if not ok:
                self.send_json_response({"error": err}, status=409)
                return

            broadcast_event("PARTY_SEATED", data)
            broadcast_event("TABLES_UPDATED", self.db.get_all_tables())
            self.send_json_response({"success": True, "data": data})
            return

        # Host Action: Mark Table Dirty (Finished Dining)
        if path == "/api/host/dirty":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            table_number = body.get("table_number")
            if not table_number:
                self.send_json_response({"error": "Missing table_number"}, status=400)
                return

            ok, err, data = self.db.mark_table_dirty(table_number=int(table_number))
            if not ok:
                self.send_json_response({"error": err}, status=409)
                return

            broadcast_event("TABLE_DIRTY", data)
            broadcast_event("TABLES_UPDATED", self.db.get_all_tables())
            self.send_json_response({"success": True, "data": data})
            return

        # Host Action: Mark Table Clean (Available for Seating)
        if path == "/api/host/clean":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            table_number = body.get("table_number")
            if not table_number:
                self.send_json_response({"error": "Missing table_number"}, status=400)
                return

            ok, err, data = self.db.clean_table(table_number=int(table_number))
            if not ok:
                self.send_json_response({"error": err}, status=409)
                return

            broadcast_event("TABLE_CLEANED", data)
            broadcast_event("TABLES_UPDATED", self.db.get_all_tables())
            self.send_json_response({"success": True, "data": data})
            return

        # Host Action: Bump Expired Party
        if path == "/api/host/bump":
            if not verify_host_auth(self.get_host_pin_from_request()):
                self.send_json_response({"error": "Unauthorized. Invalid Host PIN."}, status=401)
                return
            table_number = body.get("table_number")
            force = bool(body.get("force", False))
            if not table_number:
                self.send_json_response({"error": "Missing table_number"}, status=400)
                return

            ok, err, data = self.db.bump_expired_party(table_number=int(table_number), force=force)
            if not ok:
                self.send_json_response({"error": err}, status=409)
                return

            broadcast_event("PARTY_BUMPED", data)
            broadcast_event("TABLES_UPDATED", self.db.get_all_tables())
            self.send_json_response({"success": True, "data": data})
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def handle_sse_stream(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_cors_headers()
        self.end_headers()

        client_queue = queue.Queue(maxsize=100)
        with sse_lock:
            sse_subscribers.append(client_queue)

        try:
            # Send initial greeting
            self.wfile.write(b"event: connected\ndata: {\"connected\": true}\n\n")
            self.wfile.flush()

            while True:
                try:
                    msg = client_queue.get(timeout=20.0)
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # Keepalive heartbeat comment
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except Exception:
            pass
        finally:
            with sse_lock:
                if client_queue in sse_subscribers:
                    sse_subscribers.remove(client_queue)

    def serve_static_client(self, path: str) -> None:
        if path in ("", "/"):
            path = "/index.html"

        file_path = CLIENT_DIR / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or "application/octet-stream"
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_json_response({"error": "Not Found"}, status=404)


def create_server(host: str = "0.0.0.0", port: int = 8080, db_target: Optional[str] = None) -> ThreadingHTTPServer:
    db = DatabaseManager(db_target)
    db.initialize_schema()
    RestaurantRequestHandler.db = db
    server = ThreadingHTTPServer((host, port), RestaurantRequestHandler)
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="15-Table Restaurant Waitlist Server")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8080)), help="Port to listen on")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface")
    parser.add_argument("--db", default=None, help="Database path or URL")
    args = parser.parse_args()

    server = create_server(args.host, args.port, args.db)
    print(f"Server listening at http://{args.host}:{args.port}")
    print(f"Host PIN configured as: {HOST_PIN}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully.")
        server.server_close()
