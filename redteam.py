"""Red team tools — network scope validation and drill authorization.

Adapted from dsh-purge's lib/net-scope.js + lib/drill-grant.js:
- Network targets restricted to loopback and RFC1918 addresses
- DNS answers and subsequent tool arguments are checked
- Drill authorization is stored per-session in $HERMES_HOME/hermes-purge/
- This is application policy, not OS-level network isolation
"""

from __future__ import annotations

import ipaddress
import json
import logging
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Network scope validation (from dsh-purge's net-scope.js)
# ---------------------------------------------------------------------------

# RFC1918 + loopback + link-local + CGNAT ranges
_ALLOWED_NETS: List[ipaddress._BaseNetwork] = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC1918
    ipaddress.ip_network("172.16.0.0/12"),    # RFC1918
    ipaddress.ip_network("192.168.0.0/16"),   # RFC1918
    ipaddress.ip_network("169.254.0.0/16"),   # link-local
    ipaddress.ip_network("100.64.0.0/10"),    # CGNAT
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
]

# TLD suffixes that indicate Chinese domains (from net-scope.js)
_CN_SUFFIXES = [
    ".xn--fiqs8s", ".xn--fiqz9s", ".xn--j6w193g", ".xn--mix082f",
    ".xn--55qx5d", ".xn--io0a7i", ".xn--55qw42g", ".xn--zfr164b",
    ".xn--czru2d", ".cn", ".中国", ".公司", ".网络",
    ".hk", ".mo", ".tw",
]


def is_local_ip(ip_str: str) -> bool:
    """Check if an IP address is in a local/private range."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return any(ip in net for net in _ALLOWED_NETS)


def resolve_host(host: str) -> List[str]:
    """Resolve a hostname to IP addresses."""
    try:
        result = socket.getaddrinfo(host, None)
        ips = list({r[4][0] for r in result})
        return ips
    except socket.gaierror:
        return []


def validate_target(target: str) -> Tuple[bool, str]:
    """Validate a network target (IP or hostname).

    Returns (is_allowed, reason).
    """
    if not target:
        return False, "empty target"

    # Strip protocol prefixes
    for prefix in ("http://", "https://", "ftp://", "//"):
        if target.startswith(prefix):
            target = target[len(prefix):]
    # Strip path/port
    target = target.split("/")[0].split(":")[0].strip()

    if not target:
        return False, "empty after parsing"

    # Check if it's an IP address
    if is_local_ip(target):
        return True, "local IP"

    # If it's a hostname, resolve and check all IPs
    if not target.replace(".", "").replace("-", "").isdigit():
        ips = resolve_host(target)
        if not ips:
            return False, f"cannot resolve {target}"
        for ip in ips:
            if not is_local_ip(ip):
                return False, f"{target} resolves to non-local IP {ip}"
        return True, "hostname resolves to local IPs"

    return False, "not a local IP or resolvable hostname"


def is_cn_domain(host: str) -> bool:
    """Check if a hostname is a Chinese domain."""
    host_lower = host.lower()
    return any(host_lower.endswith(suffix) for suffix in _CN_SUFFIXES)


# ---------------------------------------------------------------------------
# Drill target registry
# ---------------------------------------------------------------------------

def _targets_file() -> Path:
    from prompt_manager import _purge_root
    return _purge_root() / "targets.json"


def add_drill_target(target: str) -> Dict[str, Any]:
    """Add a drill target (validates local scope first)."""
    allowed, reason = validate_target(target)
    if not allowed:
        raise ValueError(f"Target not allowed: {reason}")

    targets = _load_targets()
    targets[target] = {"added_at": _now(), "validated": True}
    _save_targets(targets)
    return {"target": target, "status": "added"}


def list_drill_targets() -> List[str]:
    return list(_load_targets().keys())


def remove_drill_target(target: str) -> bool:
    targets = _load_targets()
    if target in targets:
        del targets[target]
        _save_targets(targets)
        return True
    return False


def _load_targets() -> Dict[str, Any]:
    from prompt_manager import read_json
    return read_json(_targets_file(), {})


def _save_targets(targets: Dict[str, Any]) -> None:
    from prompt_manager import atomic_write_json
    atomic_write_json(_targets_file(), targets)


def _now() -> str:
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ---------------------------------------------------------------------------
# Red team capability definitions
# ---------------------------------------------------------------------------

REDTEAM_SKILLS = [
    {
        "name": "port-scan",
        "description": "Scan common ports on a local target",
        "requires_grant": True,
        "tools": ["terminal"],
    },
    {
        "name": "http-probe",
        "description": "Probe HTTP endpoints on a local target",
        "requires_grant": True,
        "tools": ["terminal", "browser"],
    },
    {
        "name": "file-enum",
        "description": "Enumerate files and directories on a local target",
        "requires_grant": True,
        "tools": ["terminal"],
    },
    {
        "name": "dns-lookup",
        "description": "DNS resolution and record lookup",
        "requires_grant": False,
        "tools": ["terminal"],
    },
]


def get_redteam_capabilities() -> List[Dict[str, Any]]:
    """Return available red team capabilities."""
    from prompt_manager import read_drill_grant
    granted = read_drill_grant()
    caps = []
    for skill in REDTEAM_SKILLS:
        caps.append({
            **skill,
            "available": granted or not skill["requires_grant"],
        })
    return caps
