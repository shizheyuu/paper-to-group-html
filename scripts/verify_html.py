#!/usr/bin/env python3
"""Verify that a generated deck is self-contained and free of placeholders."""

import argparse
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    text = args.html.read_text(encoding="utf-8")
    errors = []
    for pattern, label in [
        (r"(?:src|href)=[\"']https?://", "external resource"),
        (r"@import\s+url", "CSS import"),
        (r"\b(?:TODO|TBD|PLACEHOLDER)\b", "placeholder"),
        (r"<img(?![^>]+(?:src=[\"']data:|id=[\"']zoomed[\"']))", "non-embedded image"),
    ]:
        if re.search(pattern, text, re.I):
            errors.append(label)
    slide_count = len(re.findall(r'class="slide\s', text))
    if slide_count < 3:
        errors.append(f"too few slides ({slide_count})")
    if errors:
        raise SystemExit("Verification failed: " + ", ".join(errors))
    print(f"OK: {args.html} is offline and contains {slide_count} slides")


if __name__ == "__main__":
    main()
