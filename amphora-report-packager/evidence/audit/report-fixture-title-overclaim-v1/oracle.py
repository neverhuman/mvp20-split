#!/usr/bin/env python3
"""
amphora-report-packager -- report-fixture-title-overclaim-v1 (AUDIT_ONLY)

Attack on the STANDING claim carried by three prior receipts for this module:

  * live-runtime-diagnostic-parity-v1 (2026-07-31): "1 ACCEPT / 5 REJECT
    executed live (real Ed25519 forged-sig rejection, real NFKC fullwidth
    banned-claim rejection, envelope-hash mismatch, stripped-lock, legacy
    docs)" -- i.e. the compiled Rust report_fixture_accepted() control
    genuinely polices banned/overclaim content in a known-answer report
    fixture before it is treated as ACCEPT.
  * mission.md red-team dossier: "regulatory, supplier, procurement,
    qualification, or release overclaim. Every such case must fail closed
    or remain an explicit evidence gap."

This module re-uses -- byte-for-byte, unmodified -- the acceptance-predicate
and render re-derivation from report_packager_live_oracle.py
(evidence/audit/live-runtime-diagnostic-parity-v1/), which that prior receipt
validated as byte-EXACT against the live compiled
amphora-assurance-capabilities::diagnostics::report_fixture_accepted /
render_report (G1, result_digest match). We re-confirm today that
diagnostics.rs is BYTE-IDENTICAL to the file audited in that receipt
(sha256 4ec366110c523f30e285dd3cbca08fd199f28edb06560897cf7e17e7abe7dd89,
matching runtime_source_anchors.assurance_diagnostics_rs_sha256 recorded in
diagnostic.canonical.json of that receipt) -- so that receipt's live==oracle
byte-parity finding still applies to today's compiled binary, and this
oracle is a faithful stand-in for it.

NEW theory / hostile input: report_fixture_accepted() runs
contains_banned_claim() over payload["narrative"] ONLY (diagnostics.rs:630).
It never scans payload["title"] for a banned claim -- it only checks
title.strip() != "" (diagnostics.rs:620). But render_report() DOES emit
title verbatim as the document's H1 (diagnostics.rs:672,
"# {}\n\n".format(payload["title"])). So a known-answer fixture whose title
IS a banned regulatory/qualification overclaim, with clean narrative, still
satisfies every clause of report_fixture_accepted (hash bindings, envelope
binding, and -- reusing the ALREADY-DOCUMENTED unpinned-signing-key gap from
render-claim-lock-preservation-v1 G4 -- a fresh self-generated Ed25519
keypair whose key_id is self-derived and therefore self-consistent) and is
returned ACCEPT, with a rendered_document that literally opens with the
banned claim as its heading.

Positive/negative controls retained from the live-runtime oracle (signed-
known-answer ACCEPT, forged-signature / envelope-mismatch / stripped-lock /
normalized-banned-claim-in-NARRATIVE REJECT) to prove this run's oracle is
the SAME validated implementation, unmodified, not a weakened stand-in.
"""
import hashlib
import json
import unicodedata
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-report-packager"
FIXTURE_PATH_REL = "amphora-report-packager/reference/mvp20/fixtures/known-answer-package.v1.json"
FIXTURE = ROOT / FIXTURE_PATH_REL
DIAGNOSTICS_RS = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
PRIOR_RECEIPT_DIR = MOD / "evidence/audit/live-runtime-diagnostic-parity-v1"

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

# Deterministic adversary key (fixed seed => byte-stable two-replay gate).
# This is NOT the phase0 evaluator/reviewer key; it models a coordinated
# adversary who controls their OWN Ed25519 keypair, exactly the precondition
# already named in render-claim-lock-preservation-v1 G4 (self-derived,
# unpinned key_id).
ADVERSARY_SEED = hashlib.sha256(
    b"amphora-report-packager-title-overclaim-adversary-key-v1"
).digest()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_bytes(value) -> bytes:
    """serde_json::to_vec(canonicalize(v)): recursive key sort, compact."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def stable_hash(value) -> str:
    return sha(canonical_bytes(value))


def normalize_claim(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).lower()
    swept = "".join(c if c.isalnum() else " " for c in folded)
    return " ".join(swept.split())


def contains_banned_claim(value: str) -> bool:
    normalized = normalize_claim(value)
    return any(claim in normalized for claim in BANNED_CLAIMS)


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


def zero_authority_assertions() -> dict:
    return {lock: True for lock in REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS}


def fixture_accepted(fixture: dict) -> bool:
    """Byte-faithful re-derivation of
    amphora-assurance-capabilities::diagnostics::report_fixture_accepted,
    UNCHANGED from evidence/audit/live-runtime-diagnostic-parity-v1/
    report_packager_live_oracle.py::fixture_accepted (validated byte-exact
    against the live compiled runtime in that receipt, G1)."""
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


def sign_payload(payload: dict, seed: bytes) -> dict:
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes_raw()
    sig = sk.sign(canonical_bytes(payload))
    return {
        "algorithm": "Ed25519",
        "key_id": "report-fixture-{}".format(sha(pub)),
        "public_key_hex": pub.hex(),
        "signature_hex": sig.hex(),
    }


def build_title_overclaim_fixture(base: dict) -> dict:
    """A known-answer fixture whose NARRATIVE is clean but whose TITLE is a
    banned regulatory/qualification overclaim; self-signed by a fresh,
    deterministic adversary key (key_id self-derives, so the internal
    key_id-binding clause is satisfied without possessing the real fixture
    signing key -- same precondition documented in
    render-claim-lock-preservation-v1 G4)."""
    payload = json.loads(json.dumps(base["payload"]))
    payload["title"] = "Product Qualified Marine Coating — Audit Package"
    assert contains_banned_claim(payload["title"]), "title must trip the banned-claim lexicon"
    assert not any(
        contains_banned_claim(line) for line in payload["narrative"]
    ), "narrative must stay clean -- isolates the TITLE-only gap"
    rendered = render_report(payload)
    payload["rendered_document"] = rendered
    payload["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(rendered.encode("utf-8"))
    }
    signature = sign_payload(payload, ADVERSARY_SEED)
    return {"schema": base["schema"], "payload": payload, "signature": signature}


def run() -> dict:
    diagnostics_rs_sha256 = sha(DIAGNOSTICS_RS.read_bytes())
    prior_ground_truth = json.loads(
        (PRIOR_RECEIPT_DIR / "diagnostic.canonical.json").read_text()
    )
    prior_diagnostics_rs_sha256 = prior_ground_truth["runtime_source_anchors"][
        "assurance_diagnostics_rs_sha256"
    ]
    runtime_unchanged_since_prior_live_validation = (
        diagnostics_rs_sha256 == prior_diagnostics_rs_sha256
    )

    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)

    forged = json.loads(fixture_bytes)
    forged["signature"]["signature_hex"] = (
        "00" + forged["signature"]["signature_hex"][2:]
    )
    envelope_mismatch = json.loads(fixture_bytes)
    envelope_mismatch["payload"]["score_envelope_sha256"] = "0" * 64
    stripped_lock = json.loads(fixture_bytes)
    stripped_lock["payload"]["authority_lock"].pop("no_ranking_authority")
    banned_claim_narrative = json.loads(fixture_bytes)
    banned_claim_narrative["payload"]["narrative"].append(
        "ＰＲＯＣＵＲＥＭＥＮＴ"
        "‑ＲＥＡＤＹ"
    )
    title_overclaim = build_title_overclaim_fixture(fixture)

    calibration_expected = {
        "signed-known-answer": "ACCEPT",
        "forged-signature": "REJECT",
        "score-envelope-mismatch": "REJECT",
        "stripped-authority-lock": "REJECT",
        "normalized-banned-claim-narrative": "REJECT",
    }
    calibration_observed = {
        "signed-known-answer": outcome(fixture_accepted(fixture)),
        "forged-signature": outcome(fixture_accepted(forged)),
        "score-envelope-mismatch": outcome(fixture_accepted(envelope_mismatch)),
        "stripped-authority-lock": outcome(fixture_accepted(stripped_lock)),
        "normalized-banned-claim-narrative": outcome(
            fixture_accepted(banned_claim_narrative)
        ),
    }
    calibration_pass = calibration_expected == calibration_observed

    attack_expected = "REJECT"  # mission.md red-team dossier: overclaim must fail closed
    attack_observed = outcome(fixture_accepted(title_overclaim))
    attack_refutes_claim = attack_observed != attack_expected

    result = {
        "schema": "amphora.report-packager.title-overclaim-attack.v1",
        "study_id": "report-fixture-title-overclaim-v1",
        "module_id": MODULE,
        "authority": "AUDIT_ONLY",
        "claim_under_attack": (
            "amphora-report-packager/evidence/audit/live-runtime-diagnostic-parity-v1/"
            "live-runtime-diagnostic-parity-receipt.v1.dsse.json :: "
            "g1_outcome_labels/g1_positive_control_count+g1_negative_control_count "
            "(report_fixture_accepted genuinely polices banned/overclaim content "
            "in a known-answer report fixture) AND docs/mission.md red-team dossier "
            "clause 'regulatory, supplier, procurement, qualification, or release "
            "overclaim. Every such case must fail closed or remain an explicit "
            "evidence gap.'"
        ),
        "runtime_source_anchors": {
            "assurance_diagnostics_rs_sha256_today": diagnostics_rs_sha256,
            "assurance_diagnostics_rs_sha256_prior_receipt": prior_diagnostics_rs_sha256,
            "runtime_unchanged_since_prior_live_validation": runtime_unchanged_since_prior_live_validation,
            "fixture_path": FIXTURE_PATH_REL,
            "fixture_sha256": sha(fixture_bytes),
        },
        "calibration": {
            "purpose": (
                "prove this oracle is the SAME implementation validated byte-exact "
                "against the live compiled runtime in live-runtime-diagnostic-parity-v1 "
                "(unmodified fixture_accepted/render_report/contains_banned_claim), "
                "not a weakened stand-in"
            ),
            "expected": calibration_expected,
            "observed": calibration_observed,
            "calibration_pass": calibration_pass,
        },
        "attack": {
            "description": (
                "known-answer fixture with a banned regulatory/qualification claim "
                "('Product Qualified') placed ONLY in payload.title (narrative stays "
                "clean); self-signed with a fresh, deterministic adversary Ed25519 key "
                "so the self-derived key_id clause is satisfied"
            ),
            "hostile_fixture_title": title_overclaim["payload"]["title"],
            "hostile_fixture_narrative": title_overclaim["payload"]["narrative"],
            "hostile_fixture_rendered_document_first_line": title_overclaim["payload"][
                "rendered_document"
            ].splitlines()[0],
            "title_trips_banned_claim_lexicon": contains_banned_claim(
                title_overclaim["payload"]["title"]
            ),
            "narrative_clean": not any(
                contains_banned_claim(line)
                for line in title_overclaim["payload"]["narrative"]
            ),
            "expected_per_mission_red_team_dossier": attack_expected,
            "observed": attack_observed,
            "attack_refutes_claim": attack_refutes_claim,
            "hostile_fixture": title_overclaim,
        },
        "verdict": "CLAIM_REFUTED" if (calibration_pass and attack_refutes_claim) else "INCONCLUSIVE",
    }
    return result


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=False))
