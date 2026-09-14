#!/usr/bin/env python3
"""Inject explorer_data.json into explorer_template.html -> explorer.html.

Usage: python3 report/explorer/build_explorer.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "explorer_template.html")
DATA = os.path.join(HERE, "explorer_data.json")
OUT = os.path.join(HERE, "explorer.html")
PLACEHOLDER = "window.DATA = /*__EXPLORER_DATA__*/;"


def main() -> int:
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    if html.count(PLACEHOLDER) != 1:
        print(f"error: expected exactly one placeholder {PLACEHOLDER!r} in {TEMPLATE}", file=sys.stderr)
        return 1
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    # Keep non-ASCII as-is (smaller file, readable); escape "</" so the JSON can never
    # terminate the <script> block early.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = html.replace(PLACEHOLDER, "window.DATA = " + payload + ";")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT} ({size:,} bytes; {len(data['scenarios'])} pairs, {len(data['episodes'])} episodes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
