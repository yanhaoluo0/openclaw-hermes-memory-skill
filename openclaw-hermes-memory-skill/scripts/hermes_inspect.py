#!/usr/bin/env python3
"""
Hermes Inspector for Hook Integration

Reads Hermes memory and outputs structured JSON for consumption by the
OpenClaw hook handler (hook/handler.js).

Supports two output formats:
  --format context  → returns { prependContext: "..." } for before_prompt_build hook
  --format full     → returns full insights JSON (for debugging)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_memory(path: Path) -> List[dict]:
    if not path.exists():
        return []
    records: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def find_relevant_insights(records: List[dict], user_input: str, limit: int = 5) -> List[dict]:
    """
    Find the most relevant Hermes insights based on user input.
    Simple keyword-based relevance scoring.
    """
    if not records or not user_input:
        return []

    user_lower = user_input.lower()
    user_words = set(user_lower.split())

    scored = []
    for record in records:
        model_output = record.get("model_output", "").lower()
        combined = record.get("user_input", "").lower() + " " + model_output

        # Count keyword overlaps
        score = sum(1 for word in user_words if word in combined and len(word) > 2)
        if score > 0:
            scored.append((score, record))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:limit]]


def build_context_output(insights: List[dict], user_input: str) -> str:
    """Build prependContext string for before_prompt_build hook."""
    if not insights:
        return ""

    lines = ["【Hermes 相关经验参考】"]
    for i, item in enumerate(insights, 1):
        ts = item.get("timestamp", "")
        user = item.get("user_input", "").strip()
        model = item.get("model_output", "").strip()
        if user:
            lines.append(f"\n[{i}] {user}")
        if model:
            # Truncate long outputs
            if len(model) > 300:
                model = model[:300] + "..."
            lines.append(f"   → {model}")

    lines.append("\n【执行策略】")
    lines.append("1. 先从上述 Hermes 经验中提取可应用规则")
    lines.append("2. 如存在冲突，优先采用更具体、更新、更可执行的规则")
    lines.append("3. 若无相关经验，使用默认策略：澄清目标、分步执行、验证结果")
    lines.append("4. 回复需体现至少一条已应用经验")

    return "\n".join(lines)


def build_full_json(insights: List[dict], user_input: str) -> Dict[str, Any]:
    """Build full JSON output for debugging."""
    return {
        "user_input": user_input,
        "insights_count": len(insights),
        "insights": [
            {
                "timestamp": item.get("timestamp"),
                "user_input": item.get("user_input"),
                "model_output": item.get("model_output"),
                "conversation_id": item.get("conversation_id"),
                "project": item.get("project"),
            }
            for item in insights
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes memory inspector for hook integration")
    parser.add_argument("--user-input", required=True, help="Current user input text")
    parser.add_argument(
        "--memory-log",
        default=str(
            Path(__file__).resolve().parents[1] / "references" / "hermes_memory.jsonl"
        ),
        help="Path to jsonl memory log",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of latest memory records to include",
    )
    parser.add_argument(
        "--format",
        choices=["context", "full"],
        default="full",
        help="Output format: context (for hook) or full (for debugging)",
    )
    args = parser.parse_args()

    memory_path = Path(args.memory_log)
    records = load_memory(memory_path)

    # Find relevant insights based on user input
    relevant = find_relevant_insights(records, args.user_input, args.limit)

    if args.format == "context":
        output = build_context_output(relevant, args.user_input)
        # For before_prompt_build hook, we need to output just the string
        # The hook expects { prependContext: "..." }
        result = {"prependContext": output}
        print(json.dumps(result, ensure_ascii=False))
    else:
        result = build_full_json(relevant, args.user_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
