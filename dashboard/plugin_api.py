"""Dashboard plugin API — HTTP backend for the hermes-purge desktop plugin.

Provides REST endpoints at /api/plugins/hermes-purge/ for the desktop UI.
Uses only stdlib (http.server) — no external dependencies.
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple

from .. import prompt_manager as pm
from .. import capability as cap
from .. import redteam as rt

logger = logging.getLogger(__name__)


def handle_get(path: str) -> Tuple[int, Any]:
    """Handle GET requests."""
    if path == "/status":
        return 200, pm.get_status()
    elif path == "/rules":
        return 200, {"rules": pm.list_rules()}
    elif path == "/presets":
        return 200, {"presets": pm.list_presets()}
    elif path == "/identity":
        return 200, pm.get_identity()
    elif path == "/capabilities":
        return 200, {"capability": cap.get_capability_text()}
    elif path == "/redteam":
        return 200, {"capabilities": rt.get_redteam_capabilities(),
                      "targets": rt.list_drill_targets(),
                      "granted": pm.read_drill_grant()}
    elif path == "/override":
        return 200, {"text": pm.read_override()}
    else:
        return 404, {"error": f"Unknown path: {path}"}


def handle_post(path: str, body: Dict[str, Any]) -> Tuple[int, Any]:
    """Handle POST requests."""
    op = body.get("op", "")

    # Override management
    if path == "/override":
        if op == "save":
            text = body.get("text", "")
            pm.write_override(text)
            return 200, {"status": "saved", "length": len(text)}
        elif op == "revert":
            pm.clear_override()
            return 200, {"status": "reverted"}
        elif op == "apply":
            text = body.get("text", "")
            pm.write_override(text)
            pm.set_hung_prompt(text)
            return 200, {"status": "applied", "length": len(text)}
        else:
            return 400, {"error": f"Unknown op: {op}"}

    # Rules management
    if path == "/rules":
        if op == "add":
            name = body.get("name", "")
            prompt = body.get("prompt", "")
            conditions = body.get("conditions", {})
            return 200, pm.add_rule(name, prompt, conditions)
        elif op == "remove":
            name = body.get("name", "")
            ok = pm.remove_rule(name)
            return 200, {"status": "removed" if ok else "not_found"}
        else:
            return 400, {"error": f"Unknown op: {op}"}

    # Preset management
    if path == "/presets":
        if op == "save":
            name = body.get("name", "")
            text = body.get("override", "")
            rules = body.get("rules", [])
            return 200, pm.save_preset(name, text, rules)
        elif op == "apply":
            name = body.get("name", "")
            ok = pm.apply_preset(name)
            return 200, {"status": "applied" if ok else "not_found"}
        else:
            return 400, {"error": f"Unknown op: {op}"}

    # Identity management
    if path == "/identity":
        name = body.get("name", "")
        description = body.get("description", "")
        enabled = body.get("enabled", True)
        return 200, pm.set_identity(name, description, enabled)

    # Drill grant
    if path == "/grant":
        granted = body.get("granted", True)
        pm.write_drill_grant(granted)
        return 200, {"status": "granted" if granted else "revoked"}

    # Drill targets
    if path == "/redteam/targets":
        if op == "add":
            target = body.get("target", "")
            return 200, rt.add_drill_target(target)
        elif op == "remove":
            target = body.get("target", "")
            ok = rt.remove_drill_target(target)
            return 200, {"status": "removed" if ok else "not_found"}
        else:
            return 400, {"error": f"Unknown op: {op}"}

    return 404, {"error": f"Unknown path: {path}"}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.rstrip("/") or "/"
        # Strip query string
        if "?" in path:
            path = path.split("?")[0]
        code, data = handle_get(path)
        self._respond(code, data)

    def do_POST(self) -> None:
        path = self.path.rstrip("/") or "/"
        if "?" in path:
            path = path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(body_raw) if body_raw else {}
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid JSON body"})
            return
        code, data = handle_post(path, body)
        self._respond(code, data)

    def _respond(self, code: int, data: Any) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("hermes-purge API: %s", format % args)


def create_server(port: int = 0, host: str = "127.0.0.1") -> HTTPServer:
    """Create the HTTP server for the plugin API."""
    return HTTPServer((host, port), _Handler)
