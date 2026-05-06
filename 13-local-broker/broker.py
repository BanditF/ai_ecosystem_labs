#!/usr/bin/env python3
import argparse
import hmac
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = pathlib.Path(__file__).resolve().parent
EVENTS_PATH = ROOT / "events.jsonl"
DEFAULT_CONFIG_PATH = ROOT / "broker_config.dry-run.json"


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_config(path):
    return json.loads(path.read_text(encoding="utf-8"))


def log_event(record):
    with EVENTS_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"time": now(), **record}) + "\n")


def secret_source_label(secret_source):
    kind = secret_source.get("kind", "none")
    if kind == "env":
        return f"env:{secret_source['name']}"
    if kind == "command":
        argv = secret_source.get("argv", [])
        return "command:" + " ".join(argv[:2]) if argv else "command"
    return kind


def resolve_client_token(config):
    name = config.get("client_token_env")
    if not name:
        return None
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"client token environment variable {name} is not set")
    return value.strip()


class SecretResolver:
    def __init__(self, config):
        self.config = config
        self._cached = None

    def resolve(self):
        if self._cached is not None:
            return self._cached
        secret_source = self.config.get("secret_source", {"kind": "none"})
        kind = secret_source.get("kind", "none")
        if kind == "none":
            self._cached = None
            return None
        if kind == "env":
            name = secret_source["name"]
            value = os.environ.get(name)
            if not value:
                raise RuntimeError(f"environment variable {name} is not set")
            self._cached = value.strip()
            return self._cached
        if kind == "command":
            argv = secret_source.get("argv")
            if not argv:
                raise RuntimeError("secret command argv is missing")
            result = subprocess.run(argv, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "secret command failed")
            value = result.stdout.strip()
            if not value:
                raise RuntimeError("secret command returned empty output")
            self._cached = value
            return self._cached
        raise RuntimeError(f"unsupported secret source kind: {kind}")


class BrokerHandler(BaseHTTPRequestHandler):
    server_version = "ToyLocalBroker/0.1"

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
            log_event({"kind": "health", "path": self.path, "ok": False, "status": 404})
            return
        config = self.server.config
        self._json(
            200,
            {
                "ok": True,
                "listen": {
                    "host": config["listen_host"],
                    "port": config["listen_port"],
                },
                "mode": config["mode"],
                "upstream_base_url": config["upstream_base_url"],
                "allowed_paths": config["allowed_paths"],
                "client_auth": bool(self.server.client_token),
                "secret_source": secret_source_label(config.get("secret_source", {"kind": "none"})),
            },
        )
        log_event({"kind": "health", "path": self.path, "ok": True, "status": 200})

    def do_POST(self):
        config = self.server.config
        if self.server.client_token is not None:
            presented = self.headers.get("X-Broker-Token", "")
            if not hmac.compare_digest(presented, self.server.client_token):
                self._json(401, {"ok": False, "error": "client_token_required"})
                log_event({"kind": "request", "path": self.path, "ok": False, "status": 401})
                return
        if self.path not in config["allowed_paths"]:
            self._json(403, {"ok": False, "error": "path_not_allowed", "path": self.path})
            log_event({"kind": "request", "path": self.path, "ok": False, "status": 403})
            return

        length = int(self.headers.get("Content-Length", "0"))
        if length > config.get("max_request_bytes", 262144):
            self._json(413, {"ok": False, "error": "request_too_large"})
            log_event({"kind": "request", "path": self.path, "ok": False, "status": 413})
            return

        body = self.rfile.read(length)
        try:
            parsed_body = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "invalid_json"})
            log_event({"kind": "request", "path": self.path, "ok": False, "status": 400})
            return

        if config["mode"] == "dry_run":
            response = {
                "ok": True,
                "mode": "dry_run",
                "forward": {
                    "url": config["upstream_base_url"].rstrip("/") + self.path,
                    "path": self.path,
                    "secret_source": secret_source_label(config.get("secret_source", {"kind": "none"})),
                    "would_attach_bearer_token": config.get("secret_source", {}).get("kind") != "none",
                },
                "request": parsed_body,
            }
            self._json(200, response)
            log_event({"kind": "request", "path": self.path, "ok": True, "status": 200, "mode": "dry_run"})
            return

        try:
            secret = self.server.secret_resolver.resolve()
        except RuntimeError as error:
            self._json(500, {"ok": False, "error": "secret_unavailable", "detail": str(error)})
            log_event({"kind": "request", "path": self.path, "ok": False, "status": 500, "error": "secret_unavailable"})
            return

        upstream_url = config["upstream_base_url"].rstrip("/") + self.path
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {secret}",
        }
        for name, value in config.get("extra_headers", {}).items():
            headers[name] = value

        request = urllib.request.Request(upstream_url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=config.get("upstream_timeout_seconds", 30)) as response:
                payload = response.read()
                self.send_response(response.status)
                self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                log_event({"kind": "request", "path": self.path, "ok": True, "status": response.status, "mode": "proxy"})
        except urllib.error.HTTPError as error:
            payload = error.read()
            self.send_response(error.code)
            self.send_header("Content-Type", error.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            log_event({"kind": "request", "path": self.path, "ok": False, "status": error.code, "mode": "proxy"})
        except Exception as error:  # surfaced as explicit broker failure
            self._json(502, {"ok": False, "error": "upstream_unreachable", "detail": str(error)})
            log_event({"kind": "request", "path": self.path, "ok": False, "status": 502, "mode": "proxy"})

    def log_message(self, fmt, *args):
        return


def build_server(config):
    server = ThreadingHTTPServer((config["listen_host"], config["listen_port"]), BrokerHandler)
    server.config = config
    server.secret_resolver = SecretResolver(config)
    server.client_token = resolve_client_token(config)
    return server


def main():
    parser = argparse.ArgumentParser(description="Toy localhost capability broker.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    args = parser.parse_args()

    config = load_config(pathlib.Path(args.config))
    server = build_server(config)
    print(
        json.dumps(
            {
                "ok": True,
                "listen": f"http://{config['listen_host']}:{config['listen_port']}",
                "mode": config["mode"],
                "allowed_paths": config["allowed_paths"],
            }
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
