# OpenClaw Hermes Memory Loop

> A structured learning loop that enables continuous improvement between OpenClaw and Hermes through deterministic reference and reporting workflows.

## Overview

OpenClaw Hermes Memory Loop enforces a **two-stage mandatory workflow** that creates a continuous feedback loop between OpenClaw (an AI assistant) and Hermes (a summarization/insights system):

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Agent                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                 ┌─────────────────────┐
│   PRE-THINK       │                 │   POST-ANSWER       │
│   Load Hermes     │                 │   Report to Hermes  │
│   Insights        │                 │                     │
└───────────────────┘                 └─────────────────────┘
        ▲                                         │
        │                                         ▼
        │                          ┌─────────────────────────┐
        │                          │   Hermes Summarizer    │
        │                          │   Extracts lessons,     │
        │                          │   rules, best practices │
        │                          └─────────────────────────┘
        │                                         │
        └───────────────── JSONL Memory Log ───────┘
```

### The Loop

1. **Before Answering**: OpenClaw loads Hermes's historical insights to inform its response
2. **After Answering**: OpenClaw reports the conversation to Hermes for analysis and learning
3. **Next Iteration**: Hermes's accumulated wisdom informs OpenClaw's next response

## Quick Start

```bash
# Step 1: Before answering - load Hermes insights
python scripts/hermes_reference.py --user-input "用户当前问题"

# Step 2: After answering - report the exchange
python scripts/hermes_report.py \
  --user-input "用户原话" \
  --model-output "OpenClaw回复"
```

## Project Structure

```
openclaw-hermes-memory-skill/
├── SKILL.md                          # Skill definition
├── scripts/
│   ├── hermes_reference.py           # Generate pre-think reference
│   ├── hermes_report.py              # Build report + update index
│   ├── update_index.py               # Index generation logic
│   └── install_index.py              # Initialize skill index
└── references/
    ├── hermes_reference_template.md  # Pre-think template
    ├── hermes_report_template.md      # Report template
    └── HERMES_SKILL_INDEX.md          # Auto-generated index
```

## Key Features

### Deterministic Templates

Fixed section headers ensure Hermes can reliably parse and extract insights:

```markdown
## [HERMES_INSIGHTS]
## [USER_INPUT]
## [MODEL_OUTPUT]
```

### Auto-Generated Skill Index

The skill automatically maintains an index (`HERMES_SKILL_INDEX.md`) that OpenClaw can query to quickly locate relevant skill content:

```bash
# View current index
cat references/HERMES_SKILL_INDEX.md

# Regenerate if needed
python scripts/install_index.py --force
```

### JSONL Memory Log

Append-only log (`hermes_memory.jsonl`) records every conversation turn for Hermes to analyze.

## Workflow Details

### Pre-think Reference

```bash
python scripts/hermes_reference.py --user-input "用户问题"
```

Output includes:
- Current user input
- Historical insights from Hermes (last N turns)
- Mandatory execution policy

### Post-answer Report

```bash
python scripts/hermes_report.py \
  --user-input "用户原话" \
  --model-output "OpenClaw回复"
```

This:
1. Appends a JSONL record to the memory log
2. Updates the skill index automatically
3. Prints a structured report for Hermes

## Requirements

- Python 3.8+
- No external dependencies (uses only stdlib)

## License

MIT
