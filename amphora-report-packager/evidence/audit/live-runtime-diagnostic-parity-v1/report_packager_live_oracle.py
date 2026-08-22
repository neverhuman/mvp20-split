#!/usr/bin/env python3
"""
amphora-report-packager -- independent non-runtime oracle
live-runtime diagnostic / evaluation / mediation parity  (v1, AUDIT_ONLY)

FOURTH, DISTINCT receipt for this module, and the FIRST that EXECUTES the live
Rust runtime (via the companion probe) rather than only re-deriving it from
source bytes:

  * banned-claim-lint-parity-v1        -> lexical overclaim lint (STATIC)
  * gate-lattice-completeness-v1       -> release-predicate algebra (STATIC)
  * render-claim-lock-preservation-v1  -> packaging-map projection (STATIC)
  * this one (live-runtime-diagnostic-parity-v1)
        -> closes the residual gap all three prior receipts explicitly left
           open ("no dependency on the live Rust runtime"): does the COMPILED,
           EXECUTING runtime actually behave as the audited source bytes say?

This file is the PREDICTION side only.  Pure CPython; no Rust execution, no
probe import, no probe output read.  Every predicted byte derives from:
  * primary artifact bytes (the known-answer fixture, the four human
    deliverables) hashed/parsed directly from disk;
  * the published primitives the runtime claims to implement, re-derived
    through INDEPENDENT implementations: SHA-256 (FIPS 180-4), Ed25519
    (RFC 8032, via python-cryptography), Unicode NFKC (UAX #15, via
    unicodedata), JSON canonicalization (recursive key sort + compact
    encoding, as in amphora_core::canonicalize/stable_hash);
  * the decision clauses of report_fixture_accepted / render_report /
    evaluate_report_packager as specified in the audited source, re-expressed
    here without sharing any code with the runtime.

The companion runner compares these predictions against the live probe output
(differential testing, McKeeman 1998; N-version discrepancy detection,
Avizienis & Chen 1977) and applies the portfolio two-replay byte gate.
AUDIT_ONLY: promotes nothing, signs nothing, edits no manifest.
"""
import hashlib
import json
import unicodedata
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-report-packager"
FIXTURE_PATH_REL = "amphora-report-packager/reference/mvp20/fixtures/known-answer-package.v1.json"
FIXTURE = ROOT / FIXTURE_PATH_REL

# REPORT_ARTIFACTS == LEGACY_REPORTS: the four compile-time-embedded human
# deliverables, in the declared constant order.
ARTIFACT_PATHS = [
    "amphora-report-packager/reference/mvp20/out/CUSTOMER_FACING.tex",
    "amphora-report-packager/reference/mvp20/out/FOUNDER_FACING.tex",
    "amphora-report-packager/reference/mvp20/out/blueprint.md",
    "amphora-report-packager/reference/mvp20/out/f718_style_datasheet.md",
]

DIAGNOSTIC_SCHEMA = "amphora.deterministic-control-diagnostic.v1"
FIXTURE_SCHEMA = "amphora.report-package-known-answer.v1"
MODULE = "amphora-report-packager"

REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS = [
    "no_ranking_authority",
    "no_optimizer_authority",
    "no_release_authority",
    "no_qualification_authority",
    "no_patentability_authority",
    "fto_not_performed",
    "no_procurement_authority",
    "no_regulatory_authority",
    "no_safety_authority",
    "no_product_performance_authority",
]

BANNED_CLAIMS = [
    "phase 1",
    "procurement ready",
    "product qualified",
    "regulatory compliant",
    "fto complete",
    "patentable",
    "scientifically validated",
    "product performance proven",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# re-derived primitives (amphora-core: canonicalize / stable_hash)
# ---------------------------------------------------------------------------
def canonical_bytes(value) -> bytes:
    """serde_json::to_vec(canonicalize(v)): recursive key sort, compact."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def stable_hash(value) -> str:
    return sha(canonical_bytes(value))


# ---------------------------------------------------------------------------
# re-derived banned-claim lint (UAX #15 NFKC via unicodedata)
# ---------------------------------------------------------------------------
def normalize_claim(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).lower()
    swept = "".join(c if c.isalnum() else " " for c in folded)
    return " ".join(swept.split())


def contains_banned_claim(value: str) -> bool:
    normalized = normalize_claim(value)
    return any(claim in normalized for claim in BANNED_CLAIMS)


# ---------------------------------------------------------------------------
# re-derived packaging map (render_report)
# ---------------------------------------------------------------------------
def render_report(payload: dict) -> str:
    out = "# {}\n\n".format(payload["title"])
    for line in payload["narrative"]:
        out += line + "\n"
    out += "\nScore envelope SHA-256: `{}`\n\n## Authority lock\n\n".format(
        payload["score_envelope_sha256"]
    )
    for lock in sorted(payload["authority_lock"].keys()):
        out += "- `{}`: `{}`\n".format(
            lock, "true" if payload["authority_lock"][lock] else "false"
        )
    out += (
        "\nScientific readiness: `{}`\nDecision use: `{}`\nRanking eligible: `{}`\n"
    ).format(
        payload["scientific_readiness"],
        payload["decision_use_ceiling"],
        "true" if payload["ranking_eligible"] else "false",
    )
    return out


# ---------------------------------------------------------------------------
# re-derived acceptance predicate (report_fixture_accepted)
# ---------------------------------------------------------------------------
def zero_authority_assertions() -> dict:
    return {lock: True for lock in REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS}


def fixture_accepted(fixture: dict) -> bool:
    payload = fixture["payload"]
    signature = fixture["signature"]
    if (
        fixture["schema"] != FIXTURE_SCHEMA
        or not payload["fixture_only"]
        or payload["authoritative"]
        or payload["title"].strip() == ""
        or len(payload["score_envelopes"]) == 0
        or payload["scientific_readiness"] != "UNVALIDATED"
        or payload["decision_use_ceiling"] != "AUDIT_ONLY"
        or payload["ranking_eligible"]
        or payload["authority_lock"] != zero_authority_assertions()
        or any(contains_banned_claim(line) for line in payload["narrative"])
    ):
        return False
    score_hash = stable_hash(payload["score_envelopes"])
    rendered = render_report(payload)
    manifest = payload["canonical_hash_manifest"]
    try:
        public = bytes.fromhex(signature["public_key_hex"])
        if len(public) != 32:
            raise ValueError
    except ValueError:
        public = b"\x00" * 32
    if (
        payload["score_envelope_sha256"] != score_hash
        or payload["rendered_document"] != rendered
        or manifest.get("known-answer-report.md") != sha(rendered.encode("utf-8"))
        or len(manifest) != 1
        or signature["algorithm"] != "Ed25519"
        or signature["key_id"] != "report-fixture-{}".format(sha(public))
    ):
        return False
    try:
        raw_signature = bytes.fromhex(signature["signature_hex"])
        if len(raw_signature) != 64:
            return False
    except ValueError:
        return False
    if len(bytes.fromhex(signature["public_key_hex"])) != 32:
        return False
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(
            raw_signature, canonical_bytes(fixture["payload"])
        )
    except (InvalidSignature, ValueError):
        return False
    return True


def outcome(accepted: bool) -> str:
    return "ACCEPT" if accepted else "REJECT"


# ---------------------------------------------------------------------------
# predicted live diagnostic (report_packager_diagnostic)
# ---------------------------------------------------------------------------
def predicted_diagnostic() -> dict:
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    valid = fixture_accepted(fixture)

    forged = json.loads(fixture_bytes)
    forged["signature"]["signature_hex"] = (
        "00" + forged["signature"]["signature_hex"][2:]
    )
    envelope_mismatch = json.loads(fixture_bytes)
    envelope_mismatch["payload"]["score_envelope_sha256"] = "0" * 64
    stripped_lock = json.loads(fixture_bytes)
    stripped_lock["payload"]["authority_lock"].pop("no_ranking_authority")
    banned_claim = json.loads(fixture_bytes)
    banned_claim["payload"]["narrative"].append(
        "ＰＲＯＣＵＲＥＭＥＮＴ"
        "‑ＲＥＡＤＹ"
    )

    expected = {
        "signed-known-answer": "ACCEPT",
        "legacy-documents": "REJECT",
        "forged-signature": "REJECT",
        "score-envelope-mismatch": "REJECT",
        "stripped-authority-lock": "REJECT",
        "normalized-banned-claim": "REJECT",
    }
    observed = {
        "signed-known-answer": outcome(fixture_accepted(fixture)),
        "legacy-documents": "REJECT",
        "forged-signature": outcome(fixture_accepted(forged)),
        "score-envelope-mismatch": outcome(fixture_accepted(envelope_mismatch)),
        "stripped-authority-lock": outcome(fixture_accepted(stripped_lock)),
        "normalized-banned-claim": outcome(fixture_accepted(banned_claim)),
    }
    legacy = [
        {
            "path": path,
            "sha256": sha((ROOT / path).read_bytes()),
            "accepted": False,
            "signed": False,
        }
        for path in ARTIFACT_PATHS
    ]
    passed = valid and expected == observed
    details = {
        "fixture_input": fixture,
        "fixture_path": FIXTURE_PATH_REL,
        "fixture_sha256": sha(fixture_bytes),
        "legacy_documents": legacy,
        "legacy_accepted_count": 0,
        "legacy_signed_count": 0,
    }
    result_digest = stable_hash(
        {
            "module_id": MODULE,
            "expected_fixture_outcomes": expected,
            "observed_fixture_outcomes": observed,
            "positive_control_count": 1,
            "negative_control_count": 5,
            "zero_authority_assertions": zero_authority_assertions(),
            "details": details,
            "passed": passed,
        }
    )
    details = dict(details)
    details["result_digest"] = result_digest
    return {
        "schema": DIAGNOSTIC_SCHEMA,
        "module_id": MODULE,
        "implementation_readiness": "COMPLETE",
        "expected_fixture_outcomes": expected,
        "observed_fixture_outcomes": observed,
        "positive_control_count": 1,
        "negative_control_count": 5,
        "zero_authority_assertions": zero_authority_assertions(),
        "details": details,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# predicted live KPI evaluation (evaluate_report_packager)
# ---------------------------------------------------------------------------
def predicted_module_result() -> dict:
    artifact_bytes = {path: (ROOT / path).read_bytes() for path in ARTIFACT_PATHS}
    generated = sum(1 for b in artifact_bytes.values() if len(b) > 0)
    hashes = {path: sha(b) for path, b in artifact_bytes.items()}
    return {
        "status": "INSUFFICIENT_INPUT",
        "score_0_1": None,
        "objective_values": {},
        "metrics": {
            "scientific_applicability": "UNVALIDATED",
            "ranking_quarantine": True,
            "generated_document_count": generated,
            "signed_report_package_present": False,
            "artifact_hashes": hashes,
        },
        "gates": {
            "score_envelopes_valid": False,
            "authority_lock_present": False,
            "banned_claim_lint_pass": False,
            "signed_report_package_present": False,
        },
        "uncertainty": {},
        "missing_inputs": [
            "registry-verified score envelopes and a signed deterministic report package"
        ],
        "explanations": [
            "Human deliverables remain downstream of sealed score envelopes and authority locks."
        ],
        "source_refs": [
            "{}#sha256={}".format(path, hashes[path]) for path in ARTIFACT_PATHS
        ],
        "evidence_scope": "report_package",
    }


# ---------------------------------------------------------------------------
# predicted descriptor projection + mediation error displays
# ---------------------------------------------------------------------------
def predicted_descriptor() -> dict:
    return {
        "project": MODULE,
        "authority_ceiling": "EVIDENCE_ONLY",
        "solver_use_ceiling": "DISABLED",
        "model_readiness_ceiling": "MODEL_READINESS_ONLY",
        "ranking_eligible": False,
        "candidate_types": ["evidence_package"],
        "non_blocking_claim_locks": [
            "banned_claim_lint_required",
            "human_deliverables_downstream_only",
        ],
        "readiness": "GATED",
    }


def unsupported_display(module_id: str) -> str:
    return (
        "capability input is invalid: "
        "unsupported assurance capability module ID: {}".format(module_id)
    )


def predicted_mediation() -> dict:
    return {
        "wrong_candidate_type": {
            "is_err": True,
            "display": "candidate type is not accepted by this capability",
        },
        "unknown_module": {
            "is_err": True,
            "display": unsupported_display("unknown-module"),
        },
        "whitespace_module": {
            "is_err": True,
            "display": unsupported_display(" amphora-report-packager"),
        },
        "empty_module": {"is_err": True, "display": unsupported_display("")},
    }


def predictions() -> dict:
    return {
        "diagnostic": predicted_diagnostic(),
        "module_result": predicted_module_result(),
        "descriptor": predicted_descriptor(),
        "mediation": predicted_mediation(),
    }


if __name__ == "__main__":
    print(json.dumps(predictions(), sort_keys=True, indent=2, ensure_ascii=False))
