#!/usr/bin/env python3
"""Re-hash the deterministic omitted-data inventory against canonical xbabe2."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--captured-at", required=True)
    args = parser.parse_args()
    doc = json.loads(args.manifest.read_text())
    missing = []
    for row in doc.get("omitted", []):
        path = args.source_root / row["path"]
        if not path.is_file():
            missing.append(row["path"])
            continue
        row["size_bytes"] = path.stat().st_size
        row["sha256"] = digest(path)
    if missing:
        print("manifest source paths missing:\n" + "\n".join(missing), file=sys.stderr)
        return 1
    doc["source"] = {"git_sha": args.source_sha, "captured_at": args.captured_at,
                     "host": "xbabe2", "path": str(args.source_root)}
    args.manifest.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print("regenerated %s (%d entries)" % (args.manifest, len(doc.get("omitted", []))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
