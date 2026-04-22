# OpenClaw Hermes Memory Loop

> A structured learning loop that enables continuous improvement between OpenClaw and Hermes through deterministic reference and reporting workflows.

## Overview

This skill creates a **two-stage continuous feedback loop** between OpenClaw and Hermes:

1. **Before Answering**: OpenClaw loads Hermes's historical insights → injects into prompt context
2. **After Answering**: OpenClaw reports the conversation to Hermes → logged for analysis
3. **Learning**: Hermes analyzes logs → extracts lessons, rules, best practices
4. **Next Iteration**: Accumulated wisdom informs future OpenClaw responses

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Agent                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                         ▼
┌───────────────────┐                 ┌─────────────────────┐
│   before_prompt_  │                 │   message_sent      │
│   build hook      │                 │   hook              │
│   hermes_inspect  │                 │   hermes_report     │
│   → prependContext│                 │   → JSONL log       │
└───────────────────┘                 └─────────────────────┘
```

## Quick Start

### Option 1: Install Hook (Automatic)

```bash
cd ~/.openclaw/workspace/skills/openclaw-hermes-memory-skill/openclaw-hermes-memory-skill/hook
openclaw plugins install --link .
```

This enables automatic hook integration - no manual steps needed.

### Option 2: Manual Scripts

```bash
# Before answering
python scripts/hermes_reference.py --user-input "用户问题"

# After answering
python scripts/hermes_report.py \
  --user-input "用户原话" \
  --model-output "OpenClaw回复"
```

## Project Structure

```
openclaw-hermes-memory-skill/
├── SKILL.md                          # Skill definition & documentation
├── hook/                            # OpenClaw plugin (optional)
│   ├── openclaw.plugin.json         # Plugin manifest
│   ├── index.js                      # Plugin entry point
│   └── handler.js                    # Hook implementations
├── scripts/
│   ├── hermes_inspect.py             # Find relevant insights (hook use)
│   ├── hermes_reference.py           # Pre-think reference (manual)
│   ├── hermes_report.py              # Build report + log to JSONL
│   ├── update_index.py               # Index generation
│   └── install_index.py              # Index initialization
└── references/
    ├── hermes_reference_template.md  # Template for pre-think context
    ├── hermes_report_template.md      # Template for Hermes report
    └── hermes_memory.jsonl           # Auto-created JSONL log
```

## Key Features

### Dual Hook Integration

The `before_prompt_build` hook injects relevant Hermes insights as `prependContext` before each model response. The `message_sent` hook logs the exchange to JSONL for Hermes to analyze.

### Deterministic Templates

Fixed section headers ensure Hermes can reliably parse and extract insights:

```markdown
## [HERMES_INSIGHTS]
## [USER_INPUT]
## [MODEL_OUTPUT]
```

### Auto-Generated Skill Index

The skill maintains an index (`HERMES_SKILL_INDEX.md`) that OpenClaw can query:

```bash
cat references/HERMES_SKILL_INDEX.md
python scripts/install_index.py --force  # Regenerate
```

## Requirements

- Python 3.8+
- OpenClaw 2026.4+ (for hook plugin)
- No external dependencies (stdlib only)

## Documentation

See [SKILL.md](openclaw-hermes-memory-skill/SKILL.md) for detailed documentation including:
- Hook architecture
- Memory log format
- Troubleshooting
- Configuration options

## License

MIT
