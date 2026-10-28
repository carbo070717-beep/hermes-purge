# hermes-purge 1.0.0

**Adapted from [lllmzr/dsh-purge](https://github.com/lllmzr/dsh-purge) (original: YuJunZhiXue) — re-engineered for Hermes Agent.**

> ⚠️ **Disclaimer**: This plugin manages local prompt overrides and provides a red-team exercise console. Applying patches changes host behavior. Passing the included checks is not a guarantee that every use is risk-free. Use only on systems you own or have explicit authorization to test.

## What is this?

dsh-purge is a DeepSeek Harness plugin that manages local prompts, rules, patches and an exercise console. This project **adapts its core principles** to the [Hermes Agent](https://github.com/NousResearch/hermes-agent) framework.

### Core principles preserved from dsh-purge:

1. **System prompt override** — Replace the default system prompt with a custom operator prompt, with four-tier fallback (disk > hung > default)
2. **Atomic file operations** — Write-to-tmp + rename pattern for safe file writes
3. **Mtime-throttled cache** — 200ms cache window for high-frequency reads
4. **Network scope validation** — Drill targets restricted to loopback/RFC1918 addresses
5. **Drill authorization gate** — Must explicitly grant before using red-team features
6. **Capability protocol** — Teaches the model about available Hermes skills
7. **Identity management** — Controls model self-identification

### Key adaptations for Hermes:

| dsh-purge (Cordis/DSH) | hermes-purge (Hermes) |
|---|---|
| Cordis plugin + web client | Hermes Python plugin + desktop plugin |
| `systemPrompt` inject hook | Hermes tools + skill + config |
| Host file patching (app.asar, Cordis config) | Config-based management (no host modification) |
| JavaScript only | Python backend + JavaScript frontend |
| React web client UI | Hermes desktop plugin SDK |

## Requirements

- Hermes Agent v0.22+
- Node >= 22.13.0 (for desktop plugin)
- Python >= 3.10 (for agent plugin)

## Installation

### Option A: Local plugin install

```bash
git clone https://github.com/<your-username>/hermes-purge.git
cd hermes-purge

# Install as local plugin
hermes plugins install . --enable

# Or manually:
cp -r hermes-purge ~/.hermes/plugins/hermes-purge/
hermes config set plugins.enabled hermes-purge
```

### Option B: Direct copy

```bash
# Copy to Hermes plugins directory
cp -r hermes-purge ~/.hermes/plugins/hermes-purge/

# Enable in config.yaml
hermes config set plugins.enabled hermes-purge

# Reload desktop plugins (⌘K → "Reload desktop plugins")
```

## Quick Start

```bash
# Check status
/purge-status

# Apply a custom system prompt
/purge-apply "You are a helpful coding assistant that always provides complete solutions."

# Or from a file
/purge-apply @file:~/my-prompt.md

# Revert to default
/purge-revert

# Manage rules
/purge-rules

# Manage presets
/purge-presets

# Check identity
/purge-identity
```

## Tools

| Tool | Description |
|------|-------------|
| `purge_status` | Show plugin status |
| `purge_apply` | Apply a system prompt override |
| `purge_revert` | Revert to default system prompt |
| `purge_rules_list` | List all prompt rules |
| `purge_rules_add` | Add a new prompt rule |
| `purge_rules_remove` | Remove a prompt rule |
| `purge_preset_save` | Save a preset |
| `purge_preset_load` | Load and apply a preset |
| `purge_preset_list` | List all saved presets |
| `purge_identity_set` | Set the model's identity |
| `purge_identity_get` | Get the current identity |
| `purge_capability_list` | List available capabilities |
| `purge_drill_grant` | Grant/revoke drill authorization |

## Desktop UI

The plugin provides a desktop management pane (right sidebar) with tabs:

- **Status** — Overview of all plugin state
- **Override** — System prompt override editor
- **Rules** — Prompt rules list
- **Presets** — Saved presets list
- **Identity** — Identity editor
- **Red Team** — Drill console with authorization gate

## Data Location

All plugin data is stored in `$HERMES_HOME/hermes-purge/`:

```
hermes-purge/
├── prompts/override.md    # System prompt override
├── rules/*.json           # Prompt rules
├── presets/*.json         # Saved presets
├── identity.json          # Identity configuration
├── drill-grant.json       # Drill authorization
├── targets.json           # Drill target registry
└── config.json            # Plugin configuration
```

## Project Structure

```
hermes-purge/
├── plugin.yaml              # Plugin manifest
├── __init__.py              # Main plugin (tools, hooks, commands)
├── prompt_manager.py        # Prompt/rules/presets/identity management
├── capability.py            # Capability protocol
├── redteam.py               # Red team tools + network scope validation
├── dashboard/
│   ├── __init__.py
│   └── plugin_api.py        # HTTP backend for desktop plugin
├── desktop/
│   └── plugin.js            # Desktop management UI
├── skills/
│   └── hermes-purge/
│       └── SKILL.md         # Bundled skill
├── README.md
├── README.zh-CN.md
└── LICENSE
```

## Authorization & Safety

- **Red team drills** require explicit authorization (`/purge-drill-grant` or desktop UI)
- **Network targets** are validated to be loopback/RFC1918 only
- **DNS resolution** is checked for hostname targets
- **No host file modification** — all data is in `$HERMES_HOME/hermes-purge/`
- **Atomic writes** prevent partial file corruption

## Credits

- Original: [YuJunZhiXue/dsh-purge](https://github.com/YuJunZhiXue/dsh-purge) — Copyright (c) 2026 小杨
- Maintainer: [lllmzr/dsh-purge](https://github.com/lllmzr/dsh-purge)
- This fork: Adapted for [Hermes Agent](https://github.com/NousResearch/hermes-agent)

## License

MIT
