#!/usr/bin/env python3
"""
claude_export_to_markdown.py

Converts a Claude.ai official data export (conversations.json) into one
Markdown file per conversation, suitable for importing into Odysseus's
Documents feature (or any markdown-native tool/vault).

Usage:
    python claude_export_to_markdown.py /path/to/conversations.json /path/to/output_dir

What it does:
  - Reads conversations.json (a JSON array of conversation objects)
  - For each conversation, walks chat_messages in order
  - Extracts text from each message's `text` field and/or `content` blocks
    (the export sometimes nests text inside a `content` list of blocks)
  - Writes a Markdown file per conversation with YAML frontmatter:
      title, uuid, created_at, updated_at
  - Skips empty/malformed messages instead of crashing
  - Sanitizes filenames and de-duplicates collisions

Notes:
  - The official export zip usually contains conversations.json at the
    top level (after unzipping). Some exports also include projects.json,
    users.json, etc. -- this script only needs conversations.json.
  - Output files are safe to drop into Odysseus's data/personal_docs
    folder, or upload one-by-one through the Documents UI (respects
    ODYSSEUS_PERSONAL_UPLOAD_MAX_BYTES, default 25 MB per file -- a
    single conversation should never come close to that).
"""

import json
import os
import re
import sys
from datetime import datetime


def sanitize_filename(name: str, max_len: int = 80) -> str:
    name = name.strip() or "untitled"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", name)
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] or "untitled"


def extract_text(message: dict) -> str:
    """Pull text out of a message, handling both flat `text` and
    nested `content` block formats used across different export versions."""
    parts = []

    text = message.get("text")
    if text:
        parts.append(text.strip())

    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            block_text = block.get("text")
            if block_text:
                parts.append(block_text.strip())
            # Some exports nest tool/artifact info -- keep it minimal and
            # skip non-text block types (images, tool_use, tool_result) to
            # avoid dumping raw JSON into the markdown.

    # De-duplicate if both `text` and `content` carried the same string
    seen = []
    for p in parts:
        if p and p not in seen:
            seen.append(p)
    return "\n\n".join(seen).strip()


def format_conversation(conv: dict) -> str:
    title = conv.get("name") or "Untitled conversation"
    uuid = conv.get("uuid", "")
    created_at = conv.get("created_at", "")
    updated_at = conv.get("updated_at", "")

    lines = []
    lines.append("---")
    lines.append(f'title: "{title.replace(chr(34), chr(39))}"')
    lines.append(f"uuid: {uuid}")
    lines.append(f"created_at: {created_at}")
    lines.append(f"updated_at: {updated_at}")
    lines.append("source: Claude.ai export")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")

    messages = conv.get("chat_messages", []) or conv.get("messages", [])
    for msg in messages:
        sender = msg.get("sender", "unknown")
        role = "**You**" if sender == "human" else "**Claude**"
        text = extract_text(msg)
        if not text:
            continue
        timestamp = msg.get("created_at", "")
        header = f"### {role}" + (f" — {timestamp}" if timestamp else "")
        lines.append(header)
        lines.append("")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) != 3:
        print("Usage: python claude_export_to_markdown.py <conversations.json> <output_dir>")
        sys.exit(1)

    src_path = sys.argv[1]
    out_dir = sys.argv[2]

    if not os.path.isfile(src_path):
        print(f"Error: file not found: {src_path}")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    with open(src_path, "r", encoding="utf-8") as f:
        conversations = json.load(f)

    if not isinstance(conversations, list):
        print("Error: expected conversations.json to contain a JSON array.")
        sys.exit(1)

    used_names = {}
    written = 0
    skipped = 0

    for conv in conversations:
        title = conv.get("name") or "untitled"
        created_at = conv.get("created_at", "")
        date_prefix = ""
        if created_at:
            try:
                date_prefix = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                ).strftime("%Y-%m-%d_")
            except ValueError:
                date_prefix = ""

        base_name = date_prefix + sanitize_filename(title)
        count = used_names.get(base_name, 0)
        used_names[base_name] = count + 1
        filename = base_name if count == 0 else f"{base_name}_{count}"
        filepath = os.path.join(out_dir, filename + ".md")

        markdown = format_conversation(conv)
        if not markdown.strip():
            skipped += 1
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        written += 1

    print(f"Done. Wrote {written} markdown files to {out_dir} ({skipped} skipped as empty).")


if __name__ == "__main__":
    main()
