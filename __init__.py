"""hermes-purge — Hermes prompt management, identity override, and red-team console.

Adapted from lllmzr/dsh-purge (original: YuJunZhiXue) for the Hermes Agent framework.

Core principles preserved from dsh-purge:
- System prompt override with four-tier fallback (disk > hung > default)
- Atomic file operations (write-to-tmp + rename)
- Mtime-throttled cache for high-frequency reads
- Network scope validation (loopback/RFC1918 only)
- Drill authorization gate
- Capability protocol (teaching the model about available skills)
- Identity management (controlling model self-identification)

Hermes adaptations:
- Cordis plugin → Hermes Python plugin (plugin.yaml + __init__.py)
- Web client UI → Hermes desktop plugin (desktop/plugin.js)
- Cordis hooks → Hermes hooks (pre_session_start, pre_tool_call)
- Host patching → config-based management (no host file modification)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from . import prompt_manager as pm
from . import capability as cap
from . import redteam as rt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def _purge_status() -> str:
    """Show hermes-purge status."""
    status = pm.get_status()
    return json.dumps(status, ensure_ascii=False, indent=2)


def _purge_apply(text: str) -> str:
    """Apply a system prompt override."""
    pm.write_override(text)
    pm.set_hung_prompt(text)
    return json.dumps({
        "status": "applied",
        "length": len(text),
        "preview": text[:200],
    }, ensure_ascii=False)


def _purge_revert() -> str:
    """Revert to default system prompt."""
    pm.clear_override()
    pm.set_hung_prompt(None)
    return json.dumps({"status": "reverted", "default": pm.DEFAULT_OPERATOR_PROMPT[:120]})


def _purge_rules_list() -> str:
    """List all prompt rules."""
    rules = pm.list_rules()
    return json.dumps({"rules": rules, "count": len(rules)}, ensure_ascii=False, indent=2)


def _purge_rules_add(name: str, prompt: str, conditions: str = "") -> str:
    """Add a prompt rule."""
    cond = {}
    if conditions:
        try:
            cond = json.loads(conditions)
        except json.JSONDecodeError:
            cond = {"raw": conditions}
    rule = pm.add_rule(name, prompt, cond)
    return json.dumps({"status": "added", "rule": rule}, ensure_ascii=False)


def _purge_rules_remove(name: str) -> str:
    """Remove a prompt rule."""
    ok = pm.remove_rule(name)
    return json.dumps({"status": "removed" if ok else "not_found"})


def _purge_preset_save(name: str, override: str, rules: str = "") -> str:
    """Save a preset (override + optional rule names)."""
    rule_list = []
    if rules:
        try:
            rule_list = json.loads(rules)
        except json.JSONDecodeError:
            rule_list = [r.strip() for r in rules.split(",") if r.strip()]
    preset = pm.save_preset(name, override, rule_list)
    return json.dumps({"status": "saved", "preset": preset}, ensure_ascii=False)


def _purge_preset_load(name: str) -> str:
    """Load (and apply) a preset."""
    preset = pm.load_preset(name)
    if not preset:
        return json.dumps({"status": "not_found", "name": name})
    pm.write_override(preset["override"])
    pm.set_hung_prompt(preset["override"])
    return json.dumps({"status": "applied", "preset": preset}, ensure_ascii=False)


def _purge_preset_list() -> str:
    """List all saved presets."""
    presets = pm.list_presets()
    return json.dumps({"presets": presets, "count": len(presets)}, ensure_ascii=False, indent=2)


def _purge_identity_set(name: str, description: str = "", enabled: bool = True) -> str:
    """Set the model's identity/persona."""
    identity = pm.set_identity(name, description, enabled)
    return json.dumps({"status": "set", "identity": identity}, ensure_ascii=False)


def _purge_identity_get() -> str:
    """Get the current identity."""
    return json.dumps(pm.get_identity(), ensure_ascii=False, indent=2)


def _purge_capability_list() -> str:
    """List available capabilities and skills protocol."""
    return json.dumps({
        "capability_protocol": cap.get_capability_text(),
        "section_id": cap.get_capability_section_id(),
    }, ensure_ascii=False, indent=2)


def _purge_drill_grant(granted: bool = True) -> str:
    """Grant or revoke drill authorization."""
    pm.write_drill_grant(granted)
    return json.dumps({"status": "granted" if granted else "revoked"})


# ---------------------------------------------------------------------------
# Hook handlers
# ---------------------------------------------------------------------------

def _on_session_start(**kwargs: Any) -> None:
    """Inject capability protocol at session start.

    This hook fires when a new session begins. It ensures the capability
    protocol text is available for the model to discover and use skills.
    """
    config = pm.get_config()
    if not config.get("capability_protocol", True):
        return
    # The capability protocol is available via the purge_capability_list tool
    # and the bundled skill. No system prompt modification needed in Hermes
    # (the model already has access to skills_list and skill_view).
    logger.debug("hermes-purge: pre_session_start — capability protocol active")


def _on_pre_tool_call(tool_name: str = "", args: Optional[dict] = None, **kwargs: Any) -> None:
    """Validate network scope for red team tool calls.

    If a terminal command targets a non-local IP, log a warning.
    This is application policy, not OS-level network isolation.
    """
    if tool_name != "terminal":
        return
    config = pm.get_config()
    if not config.get("net_scope_strict", True):
        return

    cmd = (args or {}).get("command", "")
    if not cmd:
        return

    # Check for IP addresses in the command
    import re
    for match in re.finditer(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", cmd):
        ip = match.group(1)
        if not rt.is_local_ip(ip):
            logger.warning(
                "hermes-purge: terminal command targets non-local IP %s. "
                "This is application policy, not OS-level isolation.", ip
            )


# ---------------------------------------------------------------------------
# Slash command handlers
# ---------------------------------------------------------------------------

_HELP_TEXT = """\
hermes-purge — Prompt management & red-team console

Commands:
  /purge-status          Show plugin status (override, rules, presets, identity)
  /purge-apply <text>    Apply a system prompt override
  /purge-revert          Revert to default system prompt
  /purge-rules           List prompt rules
  /purge-presets         List saved presets
  /purge-identity        Get current identity

Examples:
  /purge-apply "You are a helpful coding assistant"
  /purge-apply @file:path/to/prompt.md
"""


def _handle_slash(args: str = "") -> str:
    """Handle /purge-* slash commands."""
    argv = args.strip().split()
    if not argv:
        return _HELP_TEXT

    cmd = argv[0]
    rest = " ".join(argv[1:])

    if cmd == "status":
        return _purge_status()
    elif cmd == "apply":
        # Support @file: syntax
        if rest.startswith("@file:"):
            path = rest[6:].strip()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except OSError as e:
                return f"Error reading file: {e}"
        else:
            text = rest
        if not text:
            return "Error: no text provided. Usage: /purge-apply <text>"
        return _purge_apply(text)
    elif cmd == "revert":
        return _purge_revert()
    elif cmd == "rules":
        return _purge_rules_list()
    elif cmd == "presets":
        return _purge_preset_list()
    elif cmd == "identity":
        return _purge_identity_get()
    else:
        return f"Unknown command: {cmd}\n\n{_HELP_TEXT}"


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register all tools, hooks, and commands with the Hermes plugin API."""

    # --- Tools ---
    ctx.register_tool(
        name="purge_status",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "Show hermes-purge plugin status: override, rules, presets, identity",
        },
        handler=lambda: _purge_status(),
        description="Show hermes-purge plugin status",
    )

    ctx.register_tool(
        name="purge_apply",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "System prompt override text"},
            },
            "required": ["text"],
            "description": "Apply a custom system prompt override",
        },
        handler=lambda text: _purge_apply(text),
        description="Apply a custom system prompt override",
    )

    ctx.register_tool(
        name="purge_revert",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "Revert to the default system prompt",
        },
        handler=lambda: _purge_revert(),
        description="Revert to default system prompt",
    )

    ctx.register_tool(
        name="purge_rules_list",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "List all prompt rules",
        },
        handler=lambda: _purge_rules_list(),
        description="List all prompt rules",
    )

    ctx.register_tool(
        name="purge_rules_add",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Rule name"},
                "prompt": {"type": "string", "description": "Prompt text for the rule"},
                "conditions": {"type": "string", "description": "JSON conditions (optional)"},
            },
            "required": ["name", "prompt"],
            "description": "Add a new prompt rule",
        },
        handler=lambda name, prompt, conditions="": _purge_rules_add(name, prompt, conditions),
        description="Add a new prompt rule",
    )

    ctx.register_tool(
        name="purge_rules_remove",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Rule name to remove"},
            },
            "required": ["name"],
            "description": "Remove a prompt rule",
        },
        handler=lambda name: _purge_rules_remove(name),
        description="Remove a prompt rule",
    )

    ctx.register_tool(
        name="purge_preset_save",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Preset name"},
                "override": {"type": "string", "description": "System prompt override text"},
                "rules": {"type": "string", "description": "JSON array of rule names (optional)"},
            },
            "required": ["name", "override"],
            "description": "Save a preset (override + rules)",
        },
        handler=lambda name, override, rules="": _purge_preset_save(name, override, rules),
        description="Save a preset",
    )

    ctx.register_tool(
        name="purge_preset_load",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Preset name to load"},
            },
            "required": ["name"],
            "description": "Load and apply a preset",
        },
        handler=lambda name: _purge_preset_load(name),
        description="Load and apply a preset",
    )

    ctx.register_tool(
        name="purge_preset_list",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "List all saved presets",
        },
        handler=lambda: _purge_preset_list(),
        description="List all saved presets",
    )

    ctx.register_tool(
        name="purge_identity_set",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Identity name"},
                "description": {"type": "string", "description": "Identity description"},
                "enabled": {"type": "boolean", "description": "Enable/disable identity"},
            },
            "required": ["name"],
            "description": "Set the model's identity/persona",
        },
        handler=lambda name, description="", enabled=True: _purge_identity_set(name, description, enabled),
        description="Set the model's identity/persona",
    )

    ctx.register_tool(
        name="purge_identity_get",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "Get the current identity",
        },
        handler=lambda: _purge_identity_get(),
        description="Get the current identity",
    )

    ctx.register_tool(
        name="purge_capability_list",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {},
            "description": "List available capabilities and the capability protocol",
        },
        handler=lambda: _purge_capability_list(),
        description="List available capabilities",
    )

    ctx.register_tool(
        name="purge_drill_grant",
        toolset="hermes-purge",
        schema={
            "type": "object",
            "properties": {
                "granted": {"type": "boolean", "description": "Grant or revoke"},
            },
            "required": ["granted"],
            "description": "Grant or revoke red-team drill authorization",
        },
        handler=lambda granted: _purge_drill_grant(granted),
        description="Grant or revoke drill authorization",
    )

    # --- Hooks ---
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)

    # --- Commands ---
    ctx.register_command(
        "purge",
        handler=_handle_slash,
        description="hermes-purge: prompt management & red-team console",
    )
