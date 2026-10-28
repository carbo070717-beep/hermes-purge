---
name: hermes-purge
description: "Prompt management, identity override, capability protocol, and red-team console for Hermes Agent. Adapted from dsh-purge principles."
version: 1.0.0
author: "Adapted from lllmzr/dsh-purge → Hermes port"
license: "MIT"
---

# hermes-purge

Hermes Agent prompt management, identity override, capability protocol, and red-team console.

Adapted from [lllmzr/dsh-purge](https://github.com/lllmzr/dsh-purge) (original: YuJunZhiXue) — a DeepSeek Harness jailbreak/prompt-management plugin — re-engineered for the Hermes Agent framework.

## What it does

### 1. System Prompt Override
Override the default system prompt with a custom operator prompt. The override is stored atomically and loaded with a four-tier fallback (disk > hung > default).

### 2. Prompt Rules
Manage conditional prompt rules — named prompt snippets with optional conditions. Rules are stored as JSON files and can be enabled/disabled.

### 3. Presets
Save and load preset configurations (override text + rule list). Apply a preset to instantly switch to a saved prompt configuration.

### 4. Identity Management
Control the model's self-identification. Set a custom name and description that the model uses when asked "who are you".

### 5. Capability Protocol
Teach the model about available Hermes skills. The protocol encourages the model to discover and use skills via `skills_list` and `skill_view`.

### 6. Red Team Console
Authorized red-team drill console with:
- Network scope validation (loopback/RFC1918 only)
- Drill target registry
- Authorization gate (must grant before use)

## Tools

| Tool | Description |
|------|-------------|
| `purge_status` | Show plugin status (override, rules, presets, identity) |
| `purge_apply` | Apply a custom system prompt override |
| `purge_revert` | Revert to the default system prompt |
| `purge_rules_list` | List all prompt rules |
| `purge_rules_add` | Add a new prompt rule |
| `purge_rules_remove` | Remove a prompt rule |
| `purge_preset_save` | Save a preset (override + rules) |
| `purge_preset_load` | Load and apply a preset |
| `purge_preset_list` | List all saved presets |
| `purge_identity_set` | Set the model's identity/persona |
| `purge_identity_get` | Get the current identity |
| `purge_capability_list` | List available capabilities |
| `purge_drill_grant` | Grant or revoke drill authorization |

## Slash Commands

```
/purge-status          Show plugin status
/purge-apply <text>    Apply a system prompt override
/purge-apply @file:path  Apply override from a file
/purge-revert          Revert to default system prompt
/purge-rules           List prompt rules
/purge-presets         List saved presets
/purge-identity        Get current identity
```

## Desktop UI

The plugin provides a desktop management pane with tabs for:
- **Status** — overview of override, rules, presets, identity, drill grant
- **Override** — system prompt override editor
- **Rules** — prompt rules list
- **Presets** — saved presets list
- **Identity** — identity editor
- **Red Team** — drill console with authorization gate

## Installation

```bash
# Clone the repo
git clone https://github.com/<your-username>/hermes-purge.git

# Install as a local plugin
hermes plugins install ./hermes-purge --enable

# Or copy to plugins directory
cp -r hermes-purge ~/.hermes/plugins/hermes-purge/

# Enable in config.yaml
hermes config set plugins.enabled hermes-purge

# Reload desktop plugins (⌘K → Reload desktop plugins)
```

## Data Location

All plugin data is stored in `$HERMES_HOME/hermes-purge/`:

```
hermes-purge/
├── prompts/
│   └── override.md          # System prompt override
├── rules/
│   └── *.json               # Prompt rules
├── presets/
│   └── *.json               # Saved presets
├── identity.json            # Identity configuration
├── drill-grant.json         # Drill authorization
├── targets.json             # Drill target registry
└── config.json              # Plugin configuration
```

## Principles from dsh-purge

This plugin preserves the following principles from the original dsh-purge:

1. **Atomic file operations** — write-to-tmp + rename (from core.js H19)
2. **Mtime-throttled cache** — 200ms cache window for high-frequency reads (from hungCache)
3. **Four-tier fallback** — disk > hung > default (from installHungPromptGlobal)
4. **Network scope validation** — loopback/RFC1918 only, DNS checked (from net-scope.js)
5. **Drill authorization gate** — stored per-session, not in plugin package (from drill-grant.js)
6. **Capability protocol** — teaches model about available skills (from capability-protocol.js)
7. **Identity management** — controls model self-identification (from identity.js)

## Differences from dsh-purge

| Aspect | dsh-purge | hermes-purge |
|--------|-----------|--------------|
| Framework | Cordis (`@deepseek-ai/cordis`) | Hermes Agent |
| Plugin type | Cordis plugin + web client | Hermes Python plugin + desktop plugin |
| Host patching | Modifies Cordis config, extracts app.asar | Config-based (no host file modification) |
| System prompt injection | Cordis `systemPrompt` inject hook | Hermes tool + skill |
| UI | React web client (client.js) | Hermes desktop plugin (desktop/plugin.js) |
| Language | JavaScript | Python (backend) + JavaScript (frontend) |

## License

MIT — Adapted from lllmzr/dsh-purge (original: YuJunZhiXue, Copyright (c) 2026 小杨).
The MIT license and bundled third-party notices are preserved.
