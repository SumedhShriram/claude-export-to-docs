---
name: claude-export-to-docs
description: Converts a Claude.ai data export (conversations.json) into individual Markdown documents. Use this when the user asks to import, convert, or save their Claude conversation history/export as documents, notes, or markdown files.
---

# Claude Export to Documents

Converts an official Claude.ai data export's `conversations.json` into one
Markdown file per conversation, with YAML frontmatter (title, uuid, created_at,
updated_at) and a `### **You**` / `### **Claude**` transcript underneath. The
output is meant to be saved into this workspace's Documents area so the
conversations become searchable, readable files.

## When to use this skill

Use this whenever the user asks to:
- import/convert their Claude conversation export into documents or notes
- turn `conversations.json` (or a folder from a Claude data export zip) into
  markdown
- back up or archive old Claude chats as readable files

## How to run it

1. Locate the input file. The user will usually provide a path to an unzipped
   Claude data export folder, or directly to `conversations.json` inside it.
   If you can't find it, ask the user for the path rather than guessing.
2. Pick (or ask for) an output directory — default to something like
   `./claude_docs_import/` inside the current workspace if the user doesn't
   specify one.
3. Run the converter:

   ```bash
   python3 scripts/convert.py <path/to/conversations.json> <output_dir>
   ```

4. Report how many files were written (the script prints a summary line) and
   where they landed.
5. If the user wants them saved as Documents inside this app (not just as
   loose files on disk), move/copy the resulting `.md` files into wherever
   this workspace's Documents/personal-docs storage lives, or open them one
   by one through the Documents feature if bulk file-system access to that
   storage isn't available to you.

## Notes / edge cases

- The script skips empty/malformed conversations rather than failing the
  whole batch — that's expected, not a bug.
- Conversation titles are sanitized into safe filenames; duplicate titles get
  a numeric suffix.
- It only reads `conversations.json`. Other files in a Claude export
  (`projects.json`, `users.json`, etc.) are irrelevant to this task and can be
  ignored.
- Do not attempt to parse or reproduce content from `conversations.json` by
  hand — always invoke the script, since it correctly handles nested content
  blocks and text de-duplication that vary across export versions.
