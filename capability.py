"""Capability protocol — teaches the model about available Hermes skills.

Adapted from dsh-purge's lib/capability-protocol.js:
- The capability section is injected at session start
- It lists available skills and encourages the model to discover and use them
- It tells the model to read skill files for detailed procedures
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


CAPABILITY_SECTION_ID = "hermes-purge.capability"

CAPABILITY_PROTOCOL_TEXT = """\
# Capability Protocol

You have access to a growing library of **skills** — reusable procedures that load
into this session when relevant. Skills are your primary way to accomplish complex
tasks efficiently.

## How to Use Skills

1. **Discover**: When a user asks you to do something, check if a relevant skill exists.
   Use `skills_list` to browse all available skills, or `skill_view(name)` to read one.
2. **Load**: If a skill matches the task, load it with `skill_view(name='skill-name')`
   and follow its instructions. Skills contain specialized knowledge, API endpoints,
   and proven workflows.
3. **Follow**: Once loaded, a skill's instructions become part of your context. Follow
   them precisely — they encode the user's preferred approach and quality standards.

## Available Tool Categories

- **Web**: web_search, web_extract, browser automation
- **Files**: read_file, write_file, patch, search_files
- **Terminal**: shell commands, process management
- **Code**: execute_code for Python execution
- **Memory**: persistent cross-session memory
- **Delegation**: spawn subagents for parallel work
- **Vision**: image analysis
- **Media**: audio, video, image generation

## Key Principles

- **Err on the side of loading skills** — it is always better to have context you don't
  need than to miss critical steps.
- **Skills outperform general-purpose approaches** — they contain specialized knowledge.
- **Don't reinvent** — if a skill exists for a task, use it. Don't write your own
  workflow from scratch when a proven one is available.
- **Procedures belong in skills** — when you learn a reusable workflow, save it as a
  skill for future sessions.
"""


def build_capability_section(skills_list: List[Dict[str, str]]) -> str:
    """Build the capability protocol text with a dynamic skill list."""
    if not skills_list:
        return CAPABILITY_PROTOCOL_TEXT

    skill_lines = []
    for s in skills_list[:50]:
        name = s.get("name", "")
        desc = s.get("description", "")
        category = s.get("category", "")
        if category:
            skill_lines.append(f"- **{name}** ({category}): {desc}")
        else:
            skill_lines.append(f"- **{name}**: {desc}")

    skills_block = "\n".join(skill_lines)

    return (
        CAPABILITY_PROTOCOL_TEXT
        + "\n\n## Currently Available Skills\n\n"
        + skills_block
        + "\n\nTo load a skill, use: skill_view(name='skill-name')\n"
    )


def get_capability_text() -> str:
    """Return the static capability protocol text."""
    return CAPABILITY_PROTOCOL_TEXT


def get_capability_section_id() -> str:
    return CAPABILITY_SECTION_ID
