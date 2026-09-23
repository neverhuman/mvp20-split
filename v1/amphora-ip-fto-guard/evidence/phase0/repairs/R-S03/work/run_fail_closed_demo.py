import sys
sys.path.insert(0, ".")
from run_assignee_chain_audit import run

out = run(landscape_path="mutated_landscape_fail_closed_demo.json")
row2 = [r for r in out["rows"] if r["n"] == 2][0]
print("mutated row2 chain_status:", row2["chain_status"])
print("mutated row2 rationale:", row2["rationale"][:200])
print("mutated counts:", out["counts"])
import json
from pathlib import Path
Path("diagnostic.fail_closed_demo.json").write_text(json.dumps(out, indent=2, sort_keys=True))
