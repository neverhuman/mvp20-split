"""Small integrity/claim/task objects for trusted local release directories.

No network clients, database packages, scientific fitting, or command strings.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

MAX_DOCUMENT = 8 * 1024 * 1024
SOURCE_REVISION = "9c3018dcdd17f40be27fc3c6dc7057d2d7cb05bc"
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
REQUIRED_CLAIMS = {
    "CLM-GRAPH-01", "CLM-RUNTIME-01", "CLM-AGENT-01", "CLM-KNOW-01",
    "CLM-REPLACE-01", "CLM-SEARCH-01", "CLM-REUSE-01", "CLM-BUDGET-01",
    "CLM-UI-01", "CLM-PLGA-01", "CLM-PLGA-02", "CLM-PLGA-03",
    "CLM-VERIFY-01", "CLM-ROADMAP-01",
} | {"METRIC-" + learner + "-" + arm for learner in ["RF", "LIGHTGBM"]
     for arm in ["RAW", "KIN_ALL", "KIN_MIN", "KIN_PARETO", "KIN_ALL_PARETO",
                 "KIN_ALL_PARETO_RESIDUAL"]}


class Rejected(ValueError):
    """A bounded diagnostic label, never an input payload."""


def require(condition, reason):
    if not condition:
        raise Rejected(reason)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def strict_json(raw: bytes):
    require(len(raw) <= MAX_DOCUMENT, "document_too_large")

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_key")
            result[key] = value
        return result

    def constant(_):
        raise Rejected("nonfinite_json")

    def number(value):
        result = float(value)
        require(math.isfinite(result), "nonfinite_json")
        return result

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant,
                          parse_float=number)
    except Rejected:
        raise
    except (ValueError, UnicodeError, RecursionError):
        raise Rejected("invalid_json") from None


def closed(record, keys):
    require(isinstance(record, dict) and set(record) == set(keys), "invalid_fields")


def relative_name(name: str) -> str:
    require(isinstance(name, str) and name and "\\" not in name and "\x00" not in name,
            "invalid_path")
    p = PurePosixPath(name)
    require(not p.is_absolute() and not any(x in {"", ".", ".."} for x in name.split("/")),
            "path_escape")
    require(":" not in name, "invalid_path")
    return name


def local_file(root: Path, name: str) -> Path:
    relative_name(name)
    require(not root.is_symlink(), "linked_root")
    p = root
    for part in PurePosixPath(name).parts:
        p = p / part
        require(not p.is_symlink() and not p.is_junction(), "linked_input")
    require(p.resolve().is_relative_to(root.resolve()), "path_escape")
    return p


def bounded_read(path: Path) -> bytes:
    try:
        with path.open("rb") as f:
            raw = f.read(MAX_DOCUMENT + 1)
    except OSError:
        raise Rejected("input_unavailable") from None
    require(len(raw) <= MAX_DOCUMENT, "document_too_large")
    return raw


def pointer(value, selector):
    require(isinstance(selector, str) and (selector == "" or selector.startswith("/")),
            "invalid_selector")
    try:
        for component in selector.split("/")[1:]:
            require(re.search(r"~(?![01])", component) is None, "invalid_selector")
            key = component.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                require(re.fullmatch(r"0|[1-9][0-9]*", key) is not None, "invalid_array_selector")
                value = value[int(key)]
            else:
                require(isinstance(value, dict), "missing_selector")
                value = value[key]
    except (KeyError, IndexError, TypeError, ValueError):
        raise Rejected("missing_selector") from None
    return value


@dataclass(frozen=True)
class EvidencePin:
    path: str
    sha256: str
    bytes: int

    @classmethod
    def parse(cls, record):
        closed(record, {"path", "sha256", "bytes"})
        relative_name(record["path"])
        require(isinstance(record["sha256"], str) and DIGEST.fullmatch(record["sha256"]),
                "invalid_digest")
        require(type(record["bytes"]) is int and 0 <= record["bytes"] <= MAX_DOCUMENT,
                "invalid_size")
        return cls(**record)

    def check(self, raw):
        require(len(raw) == self.bytes and sha(raw) == self.sha256, "source_hash_mismatch")


@dataclass(frozen=True)
class HistoricalExport:
    pin: EvidencePin
    transform: str
    historical_sha256: str

    def reconstruct(self, raw):
        self.pin.check(raw)
        require(isinstance(self.historical_sha256, str) and
                DIGEST.fullmatch(self.historical_sha256) is not None, "invalid_digest")
        if self.transform == "identity":
            output = raw
        elif self.transform == "lf-to-crlf-v1":
            require(b"\r" not in raw and b"\n" in raw, "wrong_line_profile")
            try:
                raw.decode("utf-8")
            except UnicodeError:
                raise Rejected("invalid_utf8") from None
            output = raw.replace(b"\n", b"\r\n")
        else:
            raise Rejected("unknown_transform")
        require(sha(output) == self.historical_sha256, "historical_hash_mismatch")
        return output


def validate_claims(registry, read_source):
    closed(registry, {"format", "source_revision", "claims"})
    require(registry["format"] == "amphora-claim-registry.v1" and
            registry["source_revision"] == SOURCE_REVISION, "unsupported_claim_profile")
    seen = set()
    require(isinstance(registry["claims"], list) and len(registry["claims"]) == 26,
            "incomplete_claim_set")
    allowed = {"source_reviewed", "recorded_acceptance", "retrospective_research", "planned"}
    for claim in registry["claims"]:
        closed(claim, {"id", "statement", "evidence_class", "scope", "sources", "metrics",
                       "mandatory_qualifiers", "editorial_status", "reviewed_by_role",
                       "verification_status", "placements"})
        require(isinstance(claim["id"], str) and claim["id"] not in seen, "duplicate_claim")
        require(all(isinstance(claim[key], str) and claim[key] for key in
                    ["statement", "scope", "reviewed_by_role"]), "invalid_claim_text")
        require(isinstance(claim["sources"], list) and isinstance(claim["metrics"], list)
                and isinstance(claim["placements"], list), "invalid_claim_shape")
        seen.add(claim["id"])
        require(isinstance(claim["evidence_class"], str) and claim["evidence_class"] in allowed, "unknown_evidence_class")
        require(claim["verification_status"] in {"inspected", "recorded_only", "not_run"},
                "verification_promotion_requires_new_profile")
        expected = {"source_reviewed": "inspected", "recorded_acceptance": "recorded_only",
                    "retrospective_research": "inspected", "planned": "not_run"}
        require(claim["verification_status"] == expected[claim["evidence_class"]],
                "verification_evidence_mismatch")
        require(claim["editorial_status"] in {"internal_candidate", "pending_release_owner"},
                "unreviewed_editorial_promotion")
        require(claim["scope"] and claim["statement"] and claim["sources"] and
                claim["placements"] and claim["reviewed_by_role"], "empty_claim_support")
        require(isinstance(claim["mandatory_qualifiers"], list) and
                claim["mandatory_qualifiers"] and all(isinstance(v, str) and v for v in
                                                     claim["mandatory_qualifiers"]),
                "mandatory_qualifier_missing")
        require(not claim["metrics"] or claim["evidence_class"] == "retrospective_research",
                "qualitative_numeric_promotion")
        paths = set()
        for item in claim["sources"]:
            pin = EvidencePin.parse(item); pin.check(read_source(pin.path)); paths.add(pin.path)
        for metric in claim["metrics"]:
            closed(metric, {"source_path", "selector", "value", "unit", "denominator",
                            "display_decimals", "study_scope"})
            require(metric["source_path"] in paths, "metric_source_unbound")
            require(metric["unit"] and metric["denominator"] and metric["study_scope"],
                    "metric_context_missing")
            value = pointer(strict_json(read_source(metric["source_path"])), metric["selector"])
            require(type(value) is type(metric["value"]) and value == metric["value"],
                    "metric_value_drift")
            require(type(metric["display_decimals"]) is int and
                    0 <= metric["display_decimals"] <= 9, "invalid_display_policy")
    require(seen == REQUIRED_CLAIMS, "incomplete_claim_set")
    return len(seen)


def validate_ledger(ledger, root):
    closed(ledger, {"format", "plan_id", "source_revision", "accounting", "phases", "tasks",
                    "evidence_registry"})
    require(ledger["format"] == "amphora-workplan.v2", "unsupported_task_profile")
    require(ledger["source_revision"] == SOURCE_REVISION, "source_revision_drift")
    require(isinstance(ledger["phases"], list) and isinstance(ledger["tasks"], list),
            "invalid_ledger_shape")
    evidence_path = local_file(root, ledger["evidence_registry"])
    evidence = strict_json(bounded_read(evidence_path))
    closed(evidence, {"format", "records"})
    require(evidence["format"] == "amphora-task-evidence.v2" and
            isinstance(evidence["records"], list), "invalid_task_evidence_registry")
    records = {}
    for item in evidence["records"]:
        closed(item, {"pin", "supports", "kind", "actor_role", "result", "code_bindings"})
        pin = EvidencePin.parse(item["pin"])
        require(pin.path not in records and isinstance(item["supports"], list),
                "duplicate_task_evidence")
        raw = bounded_read(local_file(root, pin.path)); pin.check(raw)
        require(item["kind"] in {"preparer_inspection", "mechanical_check"} and
                item["actor_role"] == "Codex preparer; no independent signoff", "invalid_evidence_actor")
        if item["kind"] == "mechanical_check":
            closed(item["result"], {"selector", "expected", "exit_selector"})
            require(item['result']['expected'] in {'PASS', 'verified', 'fresh', 'assessment_consistent'},
                    'nonpassing_acceptance_criterion')
            result = strict_json(raw)
            exit_code = pointer(result, item["result"]["exit_selector"])
            require(pointer(result, item["result"]["selector"]) == item["result"]["expected"]
                    and type(exit_code) is int and exit_code == 0, "task_receipt_failed")
            require(item["code_bindings"], "unbound_verification_code")
        else:
            require(item["result"] == "preparer_reviewed", "invalid_inspection_result")
        for binding in item["code_bindings"]:
            code = EvidencePin.parse(binding); code.check(bounded_read(local_file(root, code.path)))
        records[pin.path] = item
    membership = []
    for phase in ledger["phases"]:
        closed(phase, {"id", "name", "tasks"})
        require(isinstance(phase["id"], str) and isinstance(phase["tasks"], list), "invalid_phase_membership")
        membership.extend(phase["tasks"])
    phases = {p["id"] for p in ledger["phases"]}
    require(len(phases) == len(ledger["phases"]), "duplicate_phase")
    tasks = {}
    fields = {"id", "title", "phase", "priority", "status", "owner_role", "reviewer_role",
              "dependencies", "deliverables", "acceptance", "evidence", "source_refs",
              "execution_authority", "estimate_minutes", "failure_disposition", "scope"}
    for task in ledger["tasks"]:
        closed(task, fields)
        require(isinstance(task["id"], str) and re.fullmatch(r"DD-\d{3}", task["id"]) and task["id"] not in tasks,
                "duplicate_or_invalid_task")
        require(task["phase"] in phases and task["status"] in
                {"planned", "in_progress", "implemented", "verified", "blocked", "deferred"},
                "invalid_task_state")
        require(task["owner_role"] and task["reviewer_role"] and task["acceptance"] and
                task["source_refs"] and task["deliverables"], "incomplete_task")
        require(task["estimate_minutes"] is None or
                (isinstance(task["estimate_minutes"], list) and len(task["estimate_minutes"]) == 2
                 and all(type(v) is int and v >= 0 for v in task["estimate_minutes"])
                 and task["estimate_minutes"][0] <= task["estimate_minutes"][1]), "invalid_estimate")
        require(isinstance(task["dependencies"], list) and
                len(set(task["dependencies"])) == len(task["dependencies"]), "duplicate_dependency")
        for item in task["acceptance"]:
            closed(item, {"check_id", "command", "availability", "criteria"})
            require(item["availability"] in {"implemented", "planned", "manual"} and
                    item["criteria"] and isinstance(item["command"], list), "invalid_acceptance")
        for rel in task["deliverables"]:
            relative_name(rel)
        if task["status"] == "verified":
            approvals = {'DD-010', 'DD-047', 'DD-059', 'DD-060', 'DD-070', 'DD-080', 'DD-081'} | {
                f'DD-{number:03d}' for number in range(25, 35)}
            require(task['id'] not in approvals, 'role_approval_not_established')
            require(task["evidence"], "verified_without_evidence")
            for rel in task["evidence"]:
                require(rel in records and task["id"] in records[rel]["supports"],
                        "task_evidence_not_qualified")
        tasks[task["id"]] = task
        for reference in task['source_refs']:
            closed(reference, {'document', 'start_line', 'end_line'})
            limits = {'SPEC-A': 1097, 'SPEC-B': 1035, 'SPEC-C': 999}
            require(isinstance(reference['document'], str) and reference['document'] in limits and
                    type(reference['start_line']) is int and type(reference['end_line']) is int and
                    1 <= reference['start_line'] <= reference['end_line'] <= limits[reference['document']],
                    'invalid_specification_range')
    require(set(tasks) == {f'DD-{number:03d}' for number in range(1,94)}, 'incomplete_backlog')
    require(set(membership) == set(tasks) and len(membership) == len(tasks),
            "phase_membership_mismatch")
    for phase in ledger["phases"]:
        require(all(tasks[key]["phase"] == phase["id"] for key in phase["tasks"]),
                "phase_owner_mismatch")
    visiting, visited = set(), set()

    def visit(key):
        require(key in tasks, "missing_dependency")
        require(key not in visiting, "dependency_cycle")
        if key in visited:
            return
        visiting.add(key)
        for dependency in tasks[key]["dependencies"]:
            visit(dependency)
            if tasks[key]["status"] == "verified":
                require(tasks[dependency]["status"] == "verified", "unmet_verified_dependency")
        visiting.remove(key); visited.add(key)

    for key in tasks:
        visit(key)
    counts = {state: sum(t["status"] == state for t in tasks.values()) for state in
              ["planned", "in_progress", "implemented", "verified", "blocked", "deferred"]}
    return {"tasks": len(tasks), "status_counts": counts,
            "readiness_interpretation": "Task counts describe preparation, not investment, scientific, product or commercial readiness."}


def verify_manifest(root: Path, expected_sha256=None):
    raw_manifest = bounded_read(local_file(root, "MANIFEST.json"))
    if expected_sha256 is not None:
        require(isinstance(expected_sha256, str) and DIGEST.fullmatch(expected_sha256), "invalid_digest")
        require(sha(raw_manifest) == expected_sha256, "external_manifest_pin_mismatch")
    manifest = strict_json(raw_manifest)
    closed(manifest, {"format", "source_revision", "audience", "release_qualified", "files"})
    require(manifest["format"] == "amphora-capsule-manifest.v2", "unsupported_manifest")
    require(manifest["source_revision"] == SOURCE_REVISION, "source_revision_drift")
    require(manifest["audience"] == "internal_engineering" and
            manifest["release_qualified"] is False, "unsupported_release_claim")
    names = set()
    require(isinstance(manifest["files"], list) and 1 <= len(manifest["files"]) <= 128,
            "invalid_manifest_members")
    for item in manifest["files"]:
        pin = EvidencePin.parse(item)
        require(pin.path not in names and pin.path not in {"MANIFEST.json", "MANIFEST.sha256"},
                "duplicate_or_circular_manifest")
        names.add(pin.path); pin.check(bounded_read(local_file(root, pin.path)))
    actual = set()
    for p in root.rglob("*"):
        require(not p.is_symlink(), "linked_input")
        if p.is_file():
            actual.add(p.relative_to(root).as_posix())
    require(actual == names | {"MANIFEST.json", "MANIFEST.sha256"}, "manifest_membership_mismatch")
    detached = bounded_read(local_file(root, "MANIFEST.sha256")).decode("ascii").strip()
    require(detached == sha(bounded_read(root / "MANIFEST.json")), "manifest_digest_mismatch")
    return manifest
