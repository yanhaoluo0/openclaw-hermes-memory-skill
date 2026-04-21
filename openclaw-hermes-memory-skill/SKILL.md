---
name: openclaw-hermes-memory-loop
description: Enforce a structured learning loop between OpenClaw and Hermes with Python scripts and fixed templates. Use when the user wants OpenClaw to (1) report each user request + model answer to Hermes in a strict format for continuous summarization, and (2) load Hermes insights before thinking/answering by using a deterministic reference template.
---

# OpenClaw Hermes Memory Loop

Use this skill to enforce a deterministic two-stage workflow:

1. Before answering, load Hermes insights and build a reference prompt.
2. After answering, report the turn (user input + model output) to Hermes with a fixed template.

## Quick Start

Run from this skill directory:

```bash
python scripts/hermes_reference.py --user-input "用户当前问题"
```

Use the generated output as OpenClaw's "thinking preface".

After OpenClaw finishes response:

```bash
python scripts/hermes_report.py --user-input "用户原话" --model-output "OpenClaw回复"
```

This command prints a fixed Hermes report prompt and appends a JSONL record into the memory log.

## Workflow

### Step 1: Pre-think reference (mandatory)

1. Run `scripts/hermes_reference.py`.
2. Copy output to OpenClaw as system or developer-level context before generation.
3. Ensure the section `## [HERMES_INSIGHTS]` is present; if no memory exists, script returns default fallback instructions.

### Step 2: Post-answer report (mandatory)

1. Run `scripts/hermes_report.py` with exact user input and model output.
2. Send printed template text to Hermes without altering section headers.
3. Keep the log file for future retrieval.

## Files

- `references/hermes_report_template.md`: Fixed report template sent to Hermes.
- `references/hermes_reference_template.md`: Fixed pre-think reference template for OpenClaw.
- `scripts/hermes_report.py`: Builds report payload and writes JSONL log.
- `scripts/hermes_reference.py`: Reads latest insights and renders pre-think template.
- Runtime log `references/hermes_memory.jsonl` is auto-created at first run and is not required for packaging.

## Rules

- Keep template headers unchanged to preserve parser compatibility.
- Never skip pre-think reference stage.
- Never skip post-answer report stage.
- If user/model text contains newlines, keep content as-is; scripts safely encode JSON logs.
