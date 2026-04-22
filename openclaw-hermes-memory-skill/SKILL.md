---
name: openclaw-hermes-memory-loop
description: Enforce a structured learning loop between OpenClaw and Hermes. Before answering, load Hermes insights and inject into context. After answering, report the exchange to Hermes for continuous summarization.
---

# OpenClaw Hermes Memory Loop

Enforces a deterministic two-stage workflow that creates a continuous feedback loop between OpenClaw and Hermes:

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Agent                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                         │
        ▼                                         ▼
┌───────────────────┐                 ┌─────────────────────┐
│   before_prompt_  │                 │   message_sent      │
│   build hook:     │                 │   hook:             │
│   hermes_inspect  │                 │   hermes_report     │
│   → prependContext│                 │   → 记录到 JSONL    │
└───────────────────┘                 └─────────────────────┘
        ▲                                         │
        │                                         ▼
        │                          ┌─────────────────────────┐
        │                          │   Hermes 分析提取经验   │
        │                          │   形成可复用规则        │
        └──────────────────────────┴─────────────────────────┘
```

## Architecture

This skill consists of two components:

1. **Python Scripts** (`scripts/`) - Core logic for Hermes interaction
2. **Plugin Hook** (`hook/`) - OpenClaw plugin for automatic hook integration

## Installation

### Option 1: Automated Hook Installation (Recommended)

After cloning the skill, install the hook plugin:

```bash
cd ~/.openclaw/workspace/skills/openclaw-hermes-memory-skill/openclaw-hermes-memory-skill/hook
openclaw plugins install --link .
```

This links the hook plugin so OpenClaw can discover it.

### Option 2: Manual Usage (No Hook)

If you don't install the plugin, you can still use the scripts manually:

```bash
# Step 1: Before answering - load Hermes insights
python scripts/hermes_reference.py --user-input "用户当前问题"

# Step 2: After answering - report the exchange
python scripts/hermes_report.py \
  --user-input "用户原话" \
  --model-output "OpenClaw回复"
```

## Hook Details

### before_prompt_build

- **Trigger**: Before OpenClaw builds the prompt for the model
- **Action**: Calls `hermes_inspect.py` to find relevant Hermes insights
- **Result**: Injects `prependContext` with Hermes experience into the prompt
- **Relevance**: Uses keyword matching to find most relevant historical insights

### message_sent

- **Trigger**: After OpenClaw sends a response to the user
- **Action**: Calls `hermes_report.py` to log the exchange
- **Result**: Writes a JSONL record to `references/hermes_memory.jsonl`
- **Hermes Analysis**: The JSONL is later analyzed by Hermes to extract lessons and rules

## Files

### Scripts (`scripts/`)

| File | Description |
|------|-------------|
| `hermes_reference.py` | Generate pre-think reference (manual workflow) |
| `hermes_inspect.py` | Find relevant insights for hook integration |
| `hermes_report.py` | Build report payload, write JSONL, update index |
| `update_index.py` | Core index generation logic |
| `install_index.py` | Initialize skill index |

### Hook Plugin (`hook/`)

| File | Description |
|------|-------------|
| `openclaw.plugin.json` | Plugin manifest |
| `index.js` | Plugin entry point |
| `handler.js` | Hook implementations (before_prompt_build, message_sent) |

### References (`references/`)

| File | Description |
|------|-------------|
| `hermes_reference_template.md` | Template for pre-think context |
| `hermes_report_template.md` | Template for Hermes report |
| `hermes_memory.jsonl` | Auto-created JSONL log of all exchanges |
| `HERMES_SKILL_INDEX.md` | Auto-generated skill index |

## Memory Log Format

Each exchange is logged as a JSON line:

```json
{
  "timestamp": "2026-04-22T02:05:18.526159+00:00",
  "conversation_id": "952b3201-33de-4473-ba3f-a61e7e0b3021",
  "project": "deep-learning",
  "user_input": "用户问题",
  "model_output": "模型回答"
}
```

## Hermes Insights Format

Insights are injected as `prependContext` with this structure:

```
【Hermes 相关经验参考】

[1] 用户问题摘要
   → 模型回答摘要（truncated to 300 chars）

【执行策略】
1. 先从上述 Hermes 经验中提取可应用规则
2. 如存在冲突，优先采用更具体、更新、更可执行的规则
3. 若无相关经验，使用默认策略：澄清目标、分步执行、验证结果
4. 回复需体现至少一条已应用经验
```

## Configuration

The hook uses these environment-aware paths:
- `HERMES_MEMORY_LOG`: Override path to `hermes_memory.jsonl`
- `SKILL_ROOT`: Auto-detected from script location

## Troubleshooting

### Hook not firing

1. Check if plugin is installed: `openclaw plugins list`
2. Enable debug: Look for `[hermes-memory-loop]` in OpenClaw logs
3. Verify Python3 is available: `python3 --version`

### Hermes insights not relevant

The `hermes_inspect.py` uses simple keyword matching. For better results:
- Keep `user_input` in hermes_memory.jsonl concise
- Hermes reports should highlight key terms

### Duplicate entries in JSONL

The hook calls `hermes_report.py` on every `message_sent`. If Hermes is also reporting, you may get duplicates. Consider disabling one of the reporting paths.

## Rules

- Keep template headers unchanged to preserve parser compatibility
- Hook errors are silent/non-blocking (logged to console for debugging)
- If user/model text contains newlines, scripts safely encode JSON logs
