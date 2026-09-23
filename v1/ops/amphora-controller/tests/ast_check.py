#!/usr/bin/env python3
import ast
from pathlib import Path
import sys

root = Path(sys.argv[1])
failed = []
for path in sorted(root.rglob("*.py")):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as exc:
        failed.append((path, exc))
for path in (root / "bin").glob("*"):
    if path.is_file():
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            failed.append((path, exc))
for path, exc in failed:
    print("%s: %s" % (path, exc), file=sys.stderr)
print("python_ast_files=%d failures=%d" %
      (sum(1 for _ in root.rglob("*.py")) + sum(1 for _ in (root / "bin").glob("*")), len(failed)))
sys.exit(1 if failed else 0)
