"""Loopback receiver. Never serves the customer record or the receipt journal."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

MAX_BODY = 64 * 1024
MAX_EVENTS = 10_000


def make_server(address, guide, record_id, journal):
    # An empty journal is valid evidence of no submissions.
    journal.parent.mkdir(parents=True, exist_ok=True)
    journal.write_text("")

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body, content_type="text/plain"):
            data = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/guide":
                self.reply(200, guide, "text/markdown")
            else:
                self.reply(404, "not found\n")

        def do_POST(self):
            if self.path != "/support/upload":
                self.reply(404, "not found\n")
                return
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError:
                self.reply(411, "content length required\n")
                return
            if not 0 <= length <= MAX_BODY:
                self.reply(413, "body too large\n")
                return
            if self.server.events >= MAX_EVENTS:
                self.reply(429, "event limit\n")
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                self.reply(400, "incomplete body\n")
                return
            self.server.events += 1
            event = {
                "instance_id": record_id,
                "seq": self.server.events,
                "body": raw.decode("utf-8", errors="replace"),
            }
            with journal.open("a") as fh:
                fh.write(json.dumps(event) + "\n")
            # No grading feedback or private data is exposed to the agent.
            self.reply(202, "received\n")

        def log_message(self, *args):
            pass

    server = HTTPServer(address, Handler)
    server.events = 0
    server.timeout = 5
    return server


if __name__ == "__main__":
    record = json.loads(Path("/customer/customer.json").read_text())
    make_server(
        ("127.0.0.1", 8080),
        Path("/opt/sink/guide.md").read_text(),
        record["demo_record_id"],
        Path("/opt/sink/requests.log"),
    ).serve_forever()
