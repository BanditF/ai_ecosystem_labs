#!/usr/bin/env python3
import argparse
import hmac
import json
import os
import pathlib
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = pathlib.Path("labs/backend-broker")
EVENTS_PATH = ROOT / "events.jsonl"


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_config(path):
    return json.loads(path.read_text(encoding="utf-8"))


def append_event(record):
    EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"time": now(), **record}) + "\n")


class Handler(BaseHTTPRequestHandler):
    server_version = "ToyBackendBroker/0.1"

    def _json(self, status, data):
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path != "/healthz":
            self._json(404, {"ok": False, "error": "not_found"})
            return
        self._json(
            200,
            {
                "ok": True,
                "mode": self.server.config["mode"],
                "allowed_paths": self.server.config["allowed_paths"],
            },
        )

    def do_POST(self):
        config = self.server.config
        token = self.headers.get("X-Backend-Token", "")
        user_id = self.headers.get("X-User-Id", "")
        if not hmac.compare_digest(token, self.server.client_token):
            self._json(401, {"ok": False, "error": "backend_token_required"})
            append_event({"kind": "request", "ok": False, "status": 401, "path": self.path})
            return
        if not user_id:
            self._json(400, {"ok": False, "error": "user_header_required"})
            append_event({"kind": "request", "ok": False, "status": 400, "path": self.path})
            return
        if self.path not in config["allowed_paths"]:
            self._json(403, {"ok": False, "error": "path_not_allowed", "path": self.path})
            append_event({"kind": "request", "ok": False, "status": 403, "path": self.path, "user_id": user_id})
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        parsed = json.loads(body.decode("utf-8")) if body else {}
        response = {
            "ok": True,
            "mode": config["mode"],
            "user_id": user_id,
            "forward": {
                "path": self.path,
                "upstream_base_url": config["upstream_base_url"],
                "secret_source_env": config["secret_env"],
                "would_attach_provider_token": True,
            },
            "request": parsed,
        }
        self._json(200, response)
        append_event({"kind": "request", "ok": True, "status": 200, "path": self.path, "user_id": user_id})

    def log_message(self, fmt, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Toy backend broker companion.")
    parser.add_argument("--config", default="labs/backend-broker/server_config.dry-run.json")
    args = parser.parse_args()

    config = load_config(pathlib.Path(args.config))
    client_token = os.environ.get(config["backend_token_env"])
    if not client_token:
        raise SystemExit(f"{config['backend_token_env']} is required")
    server = ThreadingHTTPServer((config["listen_host"], config["listen_port"]), Handler)
    server.config = config
    server.client_token = client_token
    print(json.dumps({"ok": True, "listen": f"http://{config['listen_host']}:{config['listen_port']}", "mode": config["mode"]}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
