#!/usr/bin/env python3
"""
Hermes Skill Index Generator

Scans the skill directory and generates/updates HERMES_SKILL_INDEX.md.
"""

import argparse
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional


logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_file_hash(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]


def get_last_updated(file_path: Path) -> str:
    ts = file_path.stat().st_mtime
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


PYTHON_DESCRIPTIONS = {
    "hermes_reference.py": "Render pre-think reference from Hermes memory",
    "hermes_report.py": "Build Hermes report payload and append memory log",
    "update_index.py": "Generate/update Hermes skill index",
    "install_index.py": "Initialize Hermes skill index",
}


def extract_description(file_path: Path) -> str:
    name = file_path.name
    if name in PYTHON_DESCRIPTIONS:
        return PYTHON_DESCRIPTIONS[name]
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        if file_path.suffix == ".py":
            for i, line in enumerate(lines[:10]):
                line = line.strip()
                if line.startswith('"""') or line.startswith("'''"):
                    end_marker = line[:3]
                    if line.count(end_marker) >= 2:
                        return line.strip(end_marker).strip().split("\n")[0][:60]
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if end_marker in lines[j]:
                            text = "\n".join(lines[i:j])
                            return text.strip(end_marker).strip()[:60]
            for line in lines[:5]:
                line = line.strip()
                if line.startswith("#") and not line.startswith("#!") and len(line) > 3:
                    return line.lstrip("#").strip()[:60]
        elif file_path.suffix == ".md":
            for line in lines:
                line = line.strip()
                if line.startswith("#") and len(line) > 1:
                    return line.lstrip("#").strip()[:60]
        return "No description"
    except Exception as e:
        logging.debug(f"Failed to extract description from {file_path}: {e}")
        return "No description"


def extract_tags(file_path: Path, description: str) -> list[str]:
    tags: list[str] = []
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        tags.append("script")
        try:
            content = file_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("#") and not line.startswith("#!"):
                    words = line.lstrip("#").strip().split()
                    for w in words:
                        if w.startswith("@") or w.startswith("#"):
                            tags.append(w.lstrip("@#"))
                        elif len(w) > 1 and len(tags) < 3:
                            tags.append(w.lower())
        except Exception as e:
            logging.debug(f"Failed to extract tags from {file_path}: {e}")
    elif suffix == ".md":
        tags.append("template" if "template" in file_path.name else "doc")
        if "reference" in file_path.name:
            tags.append("reference")
        elif "report" in file_path.name:
            tags.append("report")
        elif "index" in file_path.name or "skill" in file_path.name.lower():
            tags.append("meta")
    elif suffix == ".jsonl":
        tags.extend(["memory", "jsonl", "auto"])
    return list(dict.fromkeys(tags))[:5]


def scan_skill_files(skill_root: Path) -> List[dict[str, Any]]:
    include_patterns = ["*.md", "*.py", "*.jsonl"]
    exclude_patterns = [".git/*", "__pycache__/*", "*.sample", "HERMES_SKILL_INDEX.md"]
    entries: list[dict[str, Any]] = []

    for pattern in include_patterns:
        for file_path in skill_root.rglob(pattern):
            if any(file_path.match(ex) for ex in exclude_patterns):
                continue
            if not file_path.is_file():
                continue
            rel_path = file_path.relative_to(skill_root)
            description = extract_description(file_path)
            tags = extract_tags(file_path, description)
            entry = {
                "filename": str(rel_path).replace("\\", "/"),
                "description": description,
                "tags": ",".join(tags),
                "last_updated": get_last_updated(file_path),
                "file_hash": get_file_hash(file_path),
            }
            entries.append(entry)
    return entries


def render_frontmatter(metadata: dict[str, Any]) -> str:
    lines = ["---", f"version: {metadata.get('version', '1.0')}", f"generated_by: {metadata.get('generated_by', 'update_index.py')}", f"last_updated: {metadata.get('last_updated', utc_now_iso())}", "---", ""]
    return "\n".join(lines)


def render_index_table(entries: List[dict[str, Any]]) -> str:
    header = "| Filename | Description | Tags | Last Updated |\n|----------|-------------|------|--------------|\n"
    rows = []
    for e in sorted(entries, key=lambda x: x["filename"]):
        filename = e["filename"]
        desc = e["description"][:60] + ("..." if len(e["description"]) > 60 else "")
        tags = e["tags"]
        updated = e["last_updated"]
        rows.append(f"| {filename} | {desc} | {tags} | {updated} |")
    return header + "\n".join(rows) + "\n"


def render_index(entries: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    parts = [
        "# Hermes Skill Index",
        "",
        "> **Warning**: This file is auto-generated. Do not edit manually.",
        "",
        render_frontmatter(metadata),
        render_index_table(entries),
        f"\n**Total Files**: {len(entries)}\n",
    ]
    return "\n".join(parts)


def update_skill_index(
    skill_root: Path,
    index_path: Path,
    *,
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
) -> dict[str, Any]:
    if not skill_root.exists():
        raise FileNotFoundError(f"Skill root not found: {skill_root}")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    entries = scan_skill_files(skill_root)
    metadata = {
        "version": "1.0",
        "generated_by": "update_index.py",
        "last_updated": utc_now_iso(),
    }
    content = render_index(entries, metadata)
    index_path.write_text(content, encoding="utf-8")
    return {
        "files_indexed": len(entries),
        "timestamp": metadata["last_updated"],
        "index_path": str(index_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate/update Hermes skill index.")
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Skill root directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output index path (default: <skill-root>/references/HERMES_SKILL_INDEX.md)",
    )
    args = parser.parse_args()
    if args.output is None:
        output = args.skill_root / "references" / "HERMES_SKILL_INDEX.md"
    else:
        output = args.output
    result = update_skill_index(args.skill_root, output)
    logging.info(f"Indexed {result['files_indexed']} files -> {result['index_path']}")


if __name__ == "__main__":
    main()
