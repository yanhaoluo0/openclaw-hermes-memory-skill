#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List


def load_template(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


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


def format_insights(records: List[dict], limit: int) -> str:
    if not records:
        return (
            "暂无 Hermes 历史经验。\n"
            "默认策略：先澄清目标，再分解步骤，执行后自检并给出下一步建议。"
        )
    recent = records[-limit:]
    lines = []
    for i, item in enumerate(recent, start=1):
        ts = item.get("timestamp", "unknown-time")
        user_input = item.get("user_input", "").strip()
        model_output = item.get("model_output", "").strip()
        lines.append(f"[{i}] timestamp={ts}")
        lines.append(f"    user: {user_input}")
        lines.append(f"    model: {model_output}")
    return "\n".join(lines)


def build_reference(template: str, user_input: str, hermes_insights: str) -> str:
    return template.format(user_input=user_input, hermes_insights=hermes_insights)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render OpenClaw pre-think reference from Hermes memory."
    )
    parser.add_argument("--user-input", required=True, help="Current user input text")
    parser.add_argument(
        "--memory-log",
        default=str(
            Path(__file__).resolve().parents[1] / "references" / "hermes_memory.jsonl"
        ),
        help="Path to jsonl memory log",
    )
    parser.add_argument(
        "--template",
        default=str(
            Path(__file__).resolve().parents[1]
            / "references"
            / "hermes_reference_template.md"
        ),
        help="Path to pre-think reference template",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of latest memory records to include",
    )
    args = parser.parse_args()

    template = load_template(Path(args.template))
    records = load_memory(Path(args.memory_log))
    insights = format_insights(records, max(1, args.limit))
    text = build_reference(template, args.user_input, insights)
    print(text)


if __name__ == "__main__":
    main()
