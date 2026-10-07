"""Preserve dedicated store volumes and routing while replacing dynamic bindings."""
import json
import os
from pathlib import Path

from amphora_deployment.persistence.port_repair import repair


if __name__=='__main__':
    root=Path(os.environ['LOCALAPPDATA'])/'Amphora/local-v2/installation'
    try:
        for kind in ('postgres','qdrant'):
            print(kind,json.dumps(repair(root,kind)),flush=True)
    except Exception:
        raise SystemExit('Store port repair failed; inspect safe journal; raw diagnostics suppressed.') from None
