#!/usr/bin/env python3
"""
Hermes Skill Index Installer

Checks if HERMES_SKILL_INDEX.md exists, generates it if missing.
Run with --force to regenerate even if it already exists.
"""

import argparse
import logging
from pathlib import Path

from update_index import update_skill_index

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ensure_index_exists(skill_root: Path, force: bool = False) -> bool:
    index_path = skill_root / "references" / "HERMES_SKILL_INDEX.md"
    if index_path.exists() and not force:
        logging.info(f"Index already exists: {index_path}")
        return False
    result = update_skill_index(skill_root, index_path)
    logging.info(f"Created index: {result['index_path']} ({result['files_indexed']} files)")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize Hermes skill index.")
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Skill root directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if index already exists",
    )
    args = parser.parse_args()
    ensure_index_exists(args.skill_root, args.force)


if __name__ == "__main__":
    main()
