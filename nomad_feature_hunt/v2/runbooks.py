from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import CAMPAIGN_PHASES


EXPECTED_NAMES = (
    "evidence-preflight",
    "jnoccio-foundry",
    "optional-jailgun",
    "sandbox-discovery",
    "adaptive-confirmation-judging",
)


def dry_run_runbooks(directory: Path) -> dict[str, Any]:
    paths = sorted(directory.glob("*.json"))
    errors: list[str] = []
    if len(paths) != 5:
        errors.append(f"found {len(paths)} JSON runbooks, expected five")
    documents: list[dict[str, Any]] = []
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"{path.name}: invalid JSON: {error}")
            continue
        documents.append(document)
        if document.get("runbook_version") != "2.0":
            errors.append(f"{path.name}: runbook_version must be 2.0")
        if not isinstance(document.get("name"), str):
            errors.append(f"{path.name}: name is required")
    names = tuple(document.get("name") for document in documents)
    if names != EXPECTED_NAMES:
        errors.append(f"runbook ordering/names differ: {names}")
    declared_phases = {
        phase
        for document in documents
        for phase in document.get("phases", [])
        if phase in CAMPAIGN_PHASES
    }
    missing_phases = set(CAMPAIGN_PHASES) - declared_phases
    if missing_phases:
        errors.append(f"internal phases missing from runbooks: {sorted(missing_phases)}")
    return {
        "valid": not errors,
        "errors": errors,
        "runbooks": len(paths),
        "names": list(names),
        "phases": sorted(declared_phases),
    }

