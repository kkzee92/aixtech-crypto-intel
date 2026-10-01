"""Tripwire for personal data and wallet identifiers in fixtures and docs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("fixtures", "docs")
PATTERNS = {
    "email": re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I),
    "wallet": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "nric": re.compile(r"\b[STFGM]\d{7}[A-Z]\b"),
    "phone": re.compile(r"(?<!\d)(?:\+65\s?)?[89]\d{7}(?!\d)"),
}


def main() -> int:
    failures: list[str] = []
    for folder in TARGETS:
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json", ".txt", ".csv"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name, pattern in PATTERNS.items():
                if pattern.search(text):
                    failures.append(f"{path.relative_to(ROOT)} matched {name}")
    if failures:
        print("\n".join(failures))
        return 1
    print("pdpa guard: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
