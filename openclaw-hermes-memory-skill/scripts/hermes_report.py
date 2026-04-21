#!/usr/bin/env python3
import argparse
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_template(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, record: dict) -> None:
    ensure_parent(path)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_report(template: str, data: dict) -> str:
    return template.format(
        timestamp=data["timestamp"],
        conversation_id=data["conversation_id"],
        project=data["project"],
        user_input=data["user_input"],
        model_output=data["model_output"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build Hermes report payload and append memory log."
    )
    parser.add_argument("--user-input", required=True, help="Original user input text")
    parser.add_argument("--model-output", required=True, help="OpenClaw output text")
    parser.add_argument(
        "--conversation-id",
        default=str(uuid.uuid4()),
        help="Conversation id. Auto-generated if omitted.",
    )
    parser.add_argument(
        "--project", default="unknown-project", help="Project name/path label"
    )
    parser.add_argument(
        "--template",
        default=str(
            Path(__file__).resolve().parents[1]
            / "references"
            / "hermes_report_template.md"
        ),
        help="Path to report template",
    )
    parser.add_argument(
        "--memory-log",
        default=str(
            Path(__file__).resolve().parents[1] / "references" / "hermes_memory.jsonl"
        ),
        help="Path to jsonl memory log",
    )
    args = parser.parse_args()

    timestamp = utc_now_iso()
    payload = {
        "timestamp": timestamp,
        "conversation_id": args.conversation_id,
        "project": args.project,
        "user_input": args.user_input,
        "model_output": args.model_output,
    }

    template_path = Path(args.template)
    memory_log = Path(args.memory_log)
    template = load_template(template_path)
    report_text = build_report(template, payload)

    append_jsonl(memory_log, payload)

    try:
        from update_index import update_skill_index
        skill_root = Path(__file__).resolve().parents[1]
        index_path = skill_root / "references" / "HERMES_SKILL_INDEX.md"
        update_skill_index(skill_root, index_path)
    except Exception as e:
        logging.warning(f"Failed to update skill index: {e}")

    print(report_text)


if __name__ == "__main__":
    main()
