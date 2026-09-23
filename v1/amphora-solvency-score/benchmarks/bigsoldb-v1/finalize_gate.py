"""Two-replay gate over the SCIENTIFIC content of the evaluation receipt.

Run A and Run B were fully independent executions of the locked pipeline. Their
receipts differ only in the volatile `wall_seconds` timing field. Stripping that
field, the two independent receipts are byte-identical -> the scientific content
reproduces exactly. This writes the canonical (timing-free) receipt and prints
its SHA-256, which is the two-replay gate value.
"""
import hashlib, json
from pathlib import Path

B = Path("amphora-solvency-score/benchmarks/bigsoldb-v1")
a = json.loads((B / "evaluation_receipt.v20.runA.json").read_text())
b = json.loads((B / "evaluation_receipt.v20.json").read_text())  # run B (current)
for d in (a, b):
    d.pop("wall_seconds", None)
ca = json.dumps(a, sort_keys=True, indent=2).encode()
cb = json.dumps(b, sort_keys=True, indent=2).encode()
ha = hashlib.sha256(ca).hexdigest()
hb = hashlib.sha256(cb).hexdigest()
assert ha == hb, f"canonical mismatch {ha} != {hb}"
(B / "evaluation_receipt.v20.canonical.json").write_bytes(cb)
print("TWO_REPLAY_GATE_CANONICAL=PASS")
print("canonical_sha256", hb)
