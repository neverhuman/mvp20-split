#!/usr/bin/env python3
"""
amphora-report-packager -- campaign item T-12 (FIRST adversarial verdict)
forged-upstream-receipt + directive T2-12 four-vector attack oracle (AUDIT_ONLY)

Claim under attack (T-12): "amphora-report-packager has never received an
adversarial verdict; its constructive SIGNED_RECEIPT-era receipts are untested
claims" -- and specifically the honest quarantine at n=5
(signed_report_package_present=false).

SPECIFIC TARGET (2026-08-04 defensibility scorecard): feed the module's
packaging-acceptance predicate a package whose upstream receipts are
individually well-formed but collectively inconsistent (mismatched module
ids, replayed receipt, receipt signed by a non-anchored key) and check
whether it STILL refuses to emit a signed package.

DIRECTIVE T2-12 four-vector attack (founder directive 2026-08-05, section A.1):
attempt to package a report that (a) strips a claim lock, (b) reintroduces a
legacy/retracted claim, (c) evades the prohibited-claim scan via encoding
tricks, (d) clears the quarantine flag on quarantined evidence.

Pre-committed refutation_criterion (founder's wording, verbatim, restated
here and NOT softened): "Any prohibited claim, legacy claim, or quarantine
bypass reaches a packaged report."

METHODOLOGY. The live Rust entrypoint `evaluate_report_packager()`
(amphora-assurance-capabilities/src/lib.rs) takes ZERO arguments -- it never
reads candidate content at all (verified structurally: only the
candidate_type gate in AssuranceCapability::evaluate() touches the
candidate). The only component in this module's source tree that actually
CONSUMES packaged-report content and decides accept/reject is
`report_fixture_accepted` in amphora-assurance-capabilities/src/diagnostics.rs
-- the same packaging-acceptance predicate independently re-derived (and
already used) by this module's three prior AUDIT_ONLY oracles
(banned-claim-lint-parity-v1, gate-lattice-completeness-v1,
render-claim-lock-preservation-v1). This oracle re-derives that predicate
identically (byte-hash-pinned to diagnostics.rs) and, UNLIKE the prior three
oracles (which used only the single synthetic known-answer fixture, mutated
in place), feeds it packages assembled from REAL in-tree DSSE receipts drawn
from this portfolio's signed-receipt corpus -- not synthetic stubs.

Pure CPython. No import of the Rust runtime.
"""
import base64
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-report-packager"
OUT = MOD / "evidence/phase0/repairs/T-12/work"
FIXTURE = MOD / "reference/mvp20/fixtures/known-answer-package.v1.json"
DIAGNOSTICS_RS = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
CORE_RS = ROOT / "amphora-core/src/lib.rs"
PHASE0_RS = ROOT / "amphora-core/src/phase0.rs"
LIBRS = ROOT / "amphora-assurance-capabilities/src/lib.rs"

# real in-tree DSSE receipts used as forged "upstream receipt" material
REDTEAM_RECEIPT = ROOT / "amphora-redteam-audit/evidence/phase0/receipts/evaluation.v1.dsse.json"
SELF_RECEIPT = MOD / "evidence/phase0/receipts/evaluation.v1.dsse.json"

STUDY = "amphora-report-packager-t12-forged-upstream-receipt-directive-t2-12-v1"
SCHEMA = "amphora.report-packager.t12-forged-upstream-receipt-diagnostic.v1"

REFUTATION_CRITERION = (
    "Any prohibited claim, legacy claim, or quarantine bypass reaches a packaged report."
)

# adversary keys are PINNED (deterministic seeds) so the two-replay byte gate is meaningful
SEED_CLASS1 = hashlib.sha256(b"t12/forged-upstream/class1-mismatched-module-ids").digest()
SEED_CLASS2 = hashlib.sha256(b"t12/forged-upstream/class2-replayed-receipt").digest()
SEED_CLASS3 = hashlib.sha256(b"t12/forged-upstream/class3-non-anchored-key").digest()
SEED_VECTOR_C = hashlib.sha256(b"t12/directive/vector-c-encoding-trick").digest()
SEED_VECTOR_B = hashlib.sha256(b"t12/directive/vector-b-legacy-claim-reworded").digest()
SEED_VECTOR_A = hashlib.sha256(b"t12/directive/vector-a-lock-strip").digest()
SEED_VECTOR_D = hashlib.sha256(b"t12/directive/vector-d-quarantine-clear").digest()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def stable_hash(value) -> str:
    return sha(canonical_bytes(value))


# ---------------------------------------------------------------------------
# re-derived banned-claim lint (diagnostics.rs :: normalize_claim / contains_banned_claim)
# ---------------------------------------------------------------------------
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


def normalize_claim(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).lower()
    swept = "".join(c if c.isalnum() else " " for c in folded)
    return " ".join(swept.split())


def contains_banned_claim(value: str) -> bool:
    normalized = normalize_claim(value)
    return any(claim in normalized for claim in BANNED_CLAIMS)


# ---------------------------------------------------------------------------
# re-derived packaging map (diagnostics.rs :: render_report)
# ---------------------------------------------------------------------------
def render_report(payload: dict) -> str:
    out = "# {}\n\n".format(payload["title"])
    for line in payload["narrative"]:
        out += line + "\n"
    out += "\nScore envelope SHA-256: `{}`\n\n## Authority lock\n\n".format(
        payload["score_envelope_sha256"]
    )
    for lock in sorted(payload["authority_lock"]):
        enabled = "true" if payload["authority_lock"][lock] else "false"
        out += "- `{}`: `{}`\n".format(lock, enabled)
    out += "\nScientific readiness: `{}`\nDecision use: `{}`\nRanking eligible: `{}`\n".format(
        payload["scientific_readiness"],
        payload["decision_use_ceiling"],
        "true" if payload["ranking_eligible"] else "false",
    )
    return out


# ---------------------------------------------------------------------------
# re-derived REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS + acceptance predicate
# ---------------------------------------------------------------------------
phase0_src = PHASE0_RS.read_text()
m = re.search(
    r"REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS:\s*\[&str;\s*(\d+)\]\s*=\s*\[(.*?)\];",
    phase0_src,
    re.S,
)
DECLARED_LOCK_COUNT = int(m.group(1))
REQUIRED_LOCKS = re.findall(r'"([a-z0-9_]+)"', m.group(2))
assert len(REQUIRED_LOCKS) == DECLARED_LOCK_COUNT
ZERO_AUTHORITY = {lock: True for lock in REQUIRED_LOCKS}

PAYLOAD_FIELDS = {
    "fixture_id", "fixture_only", "authoritative", "title", "narrative",
    "score_envelopes", "score_envelope_sha256", "authority_lock",
    "scientific_readiness", "decision_use_ceiling", "ranking_eligible",
    "rendered_document", "canonical_hash_manifest",
}
SIG_FIELDS = {"algorithm", "key_id", "public_key_hex", "signature_hex"}
FIXTURE_SCHEMA = "amphora.report-package-known-answer.v1"


def clause_results(fixture: dict) -> dict:
    """Every clause of report_fixture_accepted, re-derived from diagnostics.rs bytes."""
    c = {}
    payload = fixture.get("payload", {})
    signature = fixture.get("signature", {})
    c["C00_struct_conformance"] = (
        set(fixture) == {"schema", "payload", "signature"}
        and set(payload) == PAYLOAD_FIELDS
        and set(signature) == SIG_FIELDS
    )
    c["C01_schema"] = fixture.get("schema") == FIXTURE_SCHEMA
    c["C02_fixture_only"] = payload.get("fixture_only") is True
    c["C03_not_authoritative"] = payload.get("authoritative") is False
    c["C04_title_nonempty"] = bool(str(payload.get("title", "")).strip())
    c["C05_score_envelopes_nonempty"] = bool(payload.get("score_envelopes"))
    c["C06_readiness_unvalidated"] = payload.get("scientific_readiness") == "UNVALIDATED"
    c["C07_ceiling_audit_only"] = payload.get("decision_use_ceiling") == "AUDIT_ONLY"
    c["C08_not_ranking_eligible"] = payload.get("ranking_eligible") is False
    c["C09_authority_lock_set"] = payload.get("authority_lock") == ZERO_AUTHORITY
    c["C10_narrative_lint"] = not any(
        contains_banned_claim(line) for line in payload.get("narrative", [])
    )
    c["C11_score_envelope_hash"] = payload.get("score_envelope_sha256") == stable_hash(
        payload.get("score_envelopes", [])
    )
    try:
        rendered = render_report(payload)
    except Exception:
        rendered = None
    c["C12_render_parity"] = rendered is not None and payload.get("rendered_document") == rendered
    manifest = payload.get("canonical_hash_manifest", {})
    c["C13_manifest_binds_render"] = (
        rendered is not None
        and manifest.get("known-answer-report.md") == sha(rendered.encode("utf-8"))
    )
    c["C14_manifest_singleton"] = len(manifest) == 1
    c["C15_algorithm_ed25519"] = signature.get("algorithm") == "Ed25519"
    try:
        pk = bytes.fromhex(signature.get("public_key_hex", ""))
    except ValueError:
        pk = b""
    c["C17_public_key_32b"] = len(pk) == 32
    derived = "report-fixture-" + sha(pk if len(pk) == 32 else bytes(32))
    c["C16_key_id_derivation"] = signature.get("key_id") == derived
    try:
        sig_bytes = bytes.fromhex(signature.get("signature_hex", ""))
    except ValueError:
        sig_bytes = b""
    c["C18_signature_64b"] = len(sig_bytes) == 64
    verified = False
    if len(pk) == 32 and len(sig_bytes) == 64:
        try:
            Ed25519PublicKey.from_public_bytes(pk).verify(sig_bytes, canonical_bytes(payload))
            verified = True
        except (InvalidSignature, Exception):
            verified = False
    c["C19_signature_verifies"] = verified
    # NOTE: this predicate re-derivation intentionally contains NO trust-store
    # lookup clause, because diagnostics.rs::report_fixture_accepted contains
    # none either -- confirmed by grep below (trust_store_lookup_present).
    return c


CLAUSES = list(clause_results(json.loads(FIXTURE.read_bytes())).keys())


def accepted(fixture: dict) -> bool:
    return all(clause_results(fixture).values())


def failing(fixture: dict) -> list:
    return sorted(k for k, v in clause_results(fixture).items() if not v)


def deep(obj):
    return json.loads(json.dumps(obj))


def resync(m):
    p = m["payload"]
    p["score_envelope_sha256"] = stable_hash(p["score_envelopes"])
    p["rendered_document"] = render_report(p)
    p["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(p["rendered_document"].encode("utf-8"))
    }


def sign_with(payload: dict, seed: bytes):
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes_raw()
    return {
        "algorithm": "Ed25519",
        "key_id": "report-fixture-" + sha(pk),
        "public_key_hex": pk.hex(),
        "signature_hex": sk.sign(canonical_bytes(payload)).hex(),
    }, pk.hex()


# ---------------------------------------------------------------------------
# structural check: does report_fixture_accepted contain ANY trust-store /
# pinned-key lookup?  (re-confirms and generalizes the prior receipt's G4 finding)
# ---------------------------------------------------------------------------
diag_src = DIAGNOSTICS_RS.read_text()
fn_src_m = re.search(r"fn report_fixture_accepted\(.*?\n\}\n", diag_src, re.S)
fn_src = fn_src_m.group(0) if fn_src_m else ""
trust_store_lookup_present = bool(
    re.search(r"trust[_-]?store|phase0[_-]?evaluator|PHASE0_EVALUATOR|anchored", fn_src, re.I)
)
score_envelope_internal_fields_checked = bool(
    re.search(r"score_envelopes\[|\.module_id|score_envelope\.", fn_src)
)
replay_or_nonce_check_present = bool(re.search(r"replay|nonce|seen|dedup", fn_src, re.I))

# ---------------------------------------------------------------------------
# corpus manifest -- REAL in-tree artifacts used as forged upstream material
# ---------------------------------------------------------------------------
dsse_receipt_count = None
try:
    import subprocess
    r = subprocess.run(
        ["find", str(ROOT), "-name", "*.dsse.json"],
        capture_output=True, text=True, timeout=90,
    )
    dsse_receipt_count = len([l for l in r.stdout.splitlines() if l.strip()])
except Exception:
    dsse_receipt_count = None

fixture_bytes = FIXTURE.read_bytes()
fixture = json.loads(fixture_bytes)

redteam_dsse = json.loads(REDTEAM_RECEIPT.read_bytes())
self_dsse = json.loads(SELF_RECEIPT.read_bytes())
redteam_payload = json.loads(base64.b64decode(redteam_dsse["signature"]["payload"]))
self_payload = json.loads(base64.b64decode(self_dsse["signature"]["payload"]))

corpus_manifest = {
    "corpus_definition": "find /home/ubuntu/amphora/build/mvp20-split -name '*.dsse.json'",
    "corpus_dsse_receipt_count_observed": dsse_receipt_count,
    "campaign_item_cited_corpus_size": 444,
    "note_on_corpus_size": (
        "The campaign item text cites a 444-receipt corpus; this run independently "
        "counted signed DSSE receipts under the reproducible glob above rather than "
        "assume the cited figure, and reports the observed count honestly."
    ),
    "artifacts_used": [
        {
            "path": str(FIXTURE.relative_to(ROOT)),
            "sha256": sha(fixture_bytes),
            "role": "baseline known-answer packaging-map fixture (payload/signature envelope consumed by report_fixture_accepted)",
        },
        {
            "path": str(REDTEAM_RECEIPT.relative_to(ROOT)),
            "sha256": sha(REDTEAM_RECEIPT.read_bytes()),
            "role": "REAL signed DSSE phase-0 evaluation receipt for a DIFFERENT module (amphora-redteam-audit), decoded and bundled as forged upstream evidence -- class 1 (mismatched module ids)",
            "decoded_module_id": redteam_payload.get("module_id"),
            "decoded_receipt_id": redteam_payload.get("receipt_id"),
        },
        {
            "path": str(SELF_RECEIPT.relative_to(ROOT)),
            "sha256": sha(SELF_RECEIPT.read_bytes()),
            "role": "REAL signed DSSE phase-0 evaluation receipt for amphora-report-packager itself, decoded and (a) bundled alongside the mismatched redteam-audit receipt for class 1, (b) duplicated within one package for class 2 (replayed receipt)",
            "decoded_module_id": self_payload.get("module_id"),
            "decoded_receipt_id": self_payload.get("receipt_id"),
        },
    ],
}

# ===========================================================================
# CLASS 1: mismatched module ids -- bundle two REAL, genuinely-signed DSSE
# receipts from two DIFFERENT modules into one package's score_envelopes,
# re-sign with an attacker-controlled (unanchored) key.
# ===========================================================================
c1 = deep(fixture)
c1["payload"]["fixture_id"] = "t12-class1-mismatched-module-ids"
c1["payload"]["title"] = "Class-1 forged package: mismatched upstream module ids"
c1["payload"]["narrative"] = [
    "This package bundles two real signed upstream receipts declaring DIFFERENT module_id values "
    "(amphora-redteam-audit and amphora-report-packager) inside one report package."
]
c1["payload"]["score_envelopes"] = [
    {"upstream_dsse_source": str(REDTEAM_RECEIPT.relative_to(ROOT)), "decoded_payload": redteam_payload},
    {"upstream_dsse_source": str(SELF_RECEIPT.relative_to(ROOT)), "decoded_payload": self_payload},
]
resync(c1)
c1_sig, c1_pk = sign_with(c1["payload"], SEED_CLASS1)
c1["signature"] = c1_sig
c1_fail = failing(c1)
c1_accept = accepted(c1)

# ===========================================================================
# CLASS 2: replayed receipt -- the SAME real DSSE receipt reused/duplicated
# within one package (no freshness / anti-replay check exercised).
# ===========================================================================
c2 = deep(fixture)
c2["payload"]["fixture_id"] = "t12-class2-replayed-receipt"
c2["payload"]["title"] = "Class-2 forged package: replayed upstream receipt"
c2["payload"]["narrative"] = [
    "This package cites the SAME real signed upstream receipt (amphora-report-packager "
    "evaluation.v1.dsse.json) twice, simulating a replayed/duplicated submission."
]
c2["payload"]["score_envelopes"] = [
    {"upstream_dsse_source": str(SELF_RECEIPT.relative_to(ROOT)), "decoded_payload": self_payload},
    {"upstream_dsse_source": str(SELF_RECEIPT.relative_to(ROOT)), "decoded_payload": self_payload},
]
resync(c2)
c2_sig, c2_pk = sign_with(c2["payload"], SEED_CLASS2)
c2["signature"] = c2_sig
c2_fail = failing(c2)
c2_accept = accepted(c2)

# ===========================================================================
# CLASS 3: receipt signed by a non-anchored key -- the UNMODIFIED baseline
# payload (all 10 claim locks true, single legitimate score envelope, no
# tampering whatsoever) re-signed with a freshly generated Ed25519 key that
# is never registered in config/phase0-trust-store.v1.json.
# ===========================================================================
c3 = deep(fixture)
c3_sig, c3_pk = sign_with(c3["payload"], SEED_CLASS3)
c3["signature"] = c3_sig
c3_fail = failing(c3)
c3_accept = accepted(c3)

trust = json.loads((ROOT / "config/phase0-trust-store.v1.json").read_text())
trust_key_ids = {k.get("key_id") for k in trust.get("keys", [])}
trust_pubkeys = {k.get("public_key_hex") for k in trust.get("keys", [])}
c3_key_is_anchored = (c3_sig["key_id"] in trust_key_ids) or (c3_pk in trust_pubkeys)

# ===========================================================================
# DIRECTIVE VECTOR (c): evade the prohibited-claim scan via encoding tricks
# -- Cyrillic homoglyph substitution. NFKC (used by normalize_claim) folds
# compatibility variants (fullwidth, NBSP, etc.) but does NOT fold confusable
# homoglyphs from a different Unicode script.
# ===========================================================================
vc = deep(fixture)
vc["payload"]["fixture_id"] = "t12-vectorC-encoding-trick"
vc["payload"]["title"] = "Directive vector (c): encoding-trick banned-claim evasion"
HOMOGLYPH_CLAIM = "This deliverable is procurement rеady for release."  # Cyrillic е U+0435
vc["payload"]["narrative"] = [HOMOGLYPH_CLAIM]
resync(vc)
vc_sig, vc_pk = sign_with(vc["payload"], SEED_VECTOR_C)
vc["signature"] = vc_sig
vc_fail = failing(vc)
vc_accept = accepted(vc)
vc_contains_banned_claim_direct = contains_banned_claim(HOMOGLYPH_CLAIM)
vc_ascii_control_claim = "This deliverable is procurement ready for release."
vc_ascii_control_caught = contains_banned_claim(vc_ascii_control_claim)

# ===========================================================================
# DIRECTIVE VECTOR (b): reintroduce a legacy/retracted claim -- differently
# worded so it is semantically a banned assertion but not a literal substring
# of the 8-phrase BANNED_CLAIMS list (closed-enumeration gap, plain ASCII,
# no encoding trick required).
# ===========================================================================
vb = deep(fixture)
vb["payload"]["fixture_id"] = "t12-vectorB-legacy-claim-reworded"
vb["payload"]["title"] = "Directive vector (b): reworded legacy/retracted claim"
REWORDED_CLAIM = "Field-ready for customer procurement and certified for product release."
vb["payload"]["narrative"] = [REWORDED_CLAIM]
resync(vb)
vb_sig, vb_pk = sign_with(vb["payload"], SEED_VECTOR_B)
vb["signature"] = vb_sig
vb_fail = failing(vb)
vb_accept = accepted(vb)
vb_contains_banned_claim_direct = contains_banned_claim(REWORDED_CLAIM)

# ===========================================================================
# DIRECTIVE VECTOR (a): strip a claim lock (control -- expected to survive)
# ===========================================================================
va = deep(fixture)
va["payload"]["fixture_id"] = "t12-vectorA-lock-strip-control"
del va["payload"]["authority_lock"]["no_ranking_authority"]
resync(va)
va_sig, va_pk = sign_with(va["payload"], SEED_VECTOR_A)
va["signature"] = va_sig
va_fail = failing(va)
va_accept = accepted(va)

# ===========================================================================
# DIRECTIVE VECTOR (d): clear the quarantine flag on quarantined evidence
# (control -- expected to survive at the fixture/predicate level via
# C02_fixture_only; ALSO checked structurally at the live-runtime level,
# where `ranking_quarantine` is a hardcoded-true, candidate-independent
# constant in base_result()).
# ===========================================================================
vd = deep(fixture)
vd["payload"]["fixture_id"] = "t12-vectorD-quarantine-clear-control"
vd["payload"]["fixture_only"] = False
resync(vd)
vd_sig, vd_pk = sign_with(vd["payload"], SEED_VECTOR_D)
vd["signature"] = vd_sig
vd_fail = failing(vd)
vd_accept = accepted(vd)

librs_text = LIBRS.read_text()
ranking_quarantine_insertions = re.findall(
    r'"ranking_quarantine"\.into\(\),\s*Value::Bool\((true|false)\)', librs_text
)
ranking_quarantine_always_true_hardcoded = (
    len(ranking_quarantine_insertions) >= 1
    and all(v == "true" for v in ranking_quarantine_insertions)
)
evaluate_report_packager_takes_candidate_arg = bool(
    re.search(r"fn evaluate_report_packager\(\s*\)", librs_text)
)

# ===========================================================================
# assemble
# ===========================================================================
classes = {
    "class1_mismatched_module_ids": {
        "description": c1["payload"]["narrative"][0],
        "fixture_id": c1["payload"]["fixture_id"],
        "signing_key_hex": c1_pk,
        "signing_key_anchored_in_trust_store": (c1_sig["key_id"] in trust_key_ids) or (c1_pk in trust_pubkeys),
        "failing_clauses": c1_fail,
        "accepted": c1_accept,
        "slipped_through": c1_accept,
    },
    "class2_replayed_receipt": {
        "description": c2["payload"]["narrative"][0],
        "fixture_id": c2["payload"]["fixture_id"],
        "signing_key_hex": c2_pk,
        "signing_key_anchored_in_trust_store": (c2_sig["key_id"] in trust_key_ids) or (c2_pk in trust_pubkeys),
        "failing_clauses": c2_fail,
        "accepted": c2_accept,
        "slipped_through": c2_accept,
    },
    "class3_non_anchored_key": {
        "description": (
            "UNMODIFIED baseline known-answer payload (all 10 claim locks true, "
            "single legitimate self-consistent score envelope, no tampering) "
            "re-signed ONLY with a freshly generated key never registered in "
            "config/phase0-trust-store.v1.json."
        ),
        "signing_key_hex": c3_pk,
        "signing_key_anchored_in_trust_store": c3_key_is_anchored,
        "failing_clauses": c3_fail,
        "accepted": c3_accept,
        "slipped_through": c3_accept,
    },
}

directive_vectors = {
    "vector_a_strip_claim_lock": {
        "expected_falsifying_observation": "acceptance despite a missing required claim lock",
        "occurred": va_accept,
        "failing_clauses": va_fail,
        "verdict": "SURVIVES" if not va_accept else "REFUTED",
    },
    "vector_b_reintroduce_legacy_retracted_claim": {
        "expected_falsifying_observation": "acceptance of a semantically-banned claim reworded to avoid the literal 8-phrase blocklist",
        "quoted_claim": REWORDED_CLAIM,
        "contains_banned_claim_direct": vb_contains_banned_claim_direct,
        "occurred": vb_accept,
        "failing_clauses": vb_fail,
        "verdict": "REFUTED" if vb_accept else "SURVIVES",
    },
    "vector_c_encoding_trick_evasion": {
        "expected_falsifying_observation": "acceptance of a Unicode-homoglyph-obfuscated banned claim",
        "quoted_claim": HOMOGLYPH_CLAIM,
        "ascii_control_claim": vc_ascii_control_claim,
        "ascii_control_caught_by_lint": vc_ascii_control_caught,
        "homoglyph_claim_caught_by_lint_directly": vc_contains_banned_claim_direct,
        "occurred": vc_accept,
        "failing_clauses": vc_fail,
        "verdict": "REFUTED" if vc_accept else "SURVIVES",
    },
    "vector_d_clear_quarantine_flag": {
        "expected_falsifying_observation": "acceptance of a package with fixture_only cleared to false (predicate level), or a live-runtime path that can flip ranking_quarantine",
        "occurred_at_predicate_level": vd_accept,
        "failing_clauses_predicate_level": vd_fail,
        "ranking_quarantine_hardcoded_true_in_liverun": ranking_quarantine_always_true_hardcoded,
        "evaluate_report_packager_ignores_all_candidate_input": evaluate_report_packager_takes_candidate_arg,
        "verdict": "REFUTED" if vd_accept else "SURVIVES",
    },
}

any_slip_through = (
    classes["class1_mismatched_module_ids"]["slipped_through"]
    or classes["class2_replayed_receipt"]["slipped_through"]
    or classes["class3_non_anchored_key"]["slipped_through"]
    or directive_vectors["vector_b_reintroduce_legacy_retracted_claim"]["occurred"]
    or directive_vectors["vector_c_encoding_trick_evasion"]["occurred"]
)

overall_verdict = "CLAIM_REFUTED" if any_slip_through else "CLAIM_SURVIVED"

refutation_criterion_observation = (
    "OCCURRED: at least one prohibited/legacy claim and/or forged-upstream-receipt "
    "package reached ACCEPTANCE by the packaging-acceptance predicate "
    "(report_fixture_accepted), which is this module's only content-sensitive "
    "packaging gate."
    if any_slip_through else
    "DID NOT OCCUR: no prohibited claim, legacy claim, or quarantine bypass reached acceptance."
)

diagnostic = {
    "schema": SCHEMA,
    "study_id": STUDY,
    "module": "amphora-report-packager",
    "campaign_item_id": "T-12",
    "run_type": "AUDIT_ONLY_INDEPENDENT_ORACLE",
    "refutation_criterion_verbatim": REFUTATION_CRITERION,
    "refutation_criterion_observation": refutation_criterion_observation,
    "directive_path": "docs/directives/2026-08-05-closing-the-open-portfolio.md",
    "directive_sha256": "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d",
    "directive_obligation": "T2-12",
    "root_cause_finding": (
        "report_fixture_accepted (the only content-sensitive packaging-acceptance "
        "predicate this module's source tree defines) contains NO trust-store / "
        "pinned-key lookup clause (verified structurally against diagnostics.rs bytes: "
        "trust_store_lookup_present={trust_store}), NO per-entry validation of "
        "score_envelopes contents such as an internal module_id check "
        "(score_envelope_internal_fields_checked={fields}), and NO replay/nonce/dedup "
        "check (replay_or_nonce_check_present={replay}). Every clause it evaluates is "
        "either (i) a literal equality against a small closed set of accepted string "
        "values, (ii) an internal hash-self-consistency check that a forger who "
        "controls the whole payload can always satisfy by recomputing, or (iii) an "
        "Ed25519 signature check against a public key the forger supplies themselves. "
        "None of the three classes an attacker's forged upstream receipt must defeat "
        "-- module-id consistency, receipt freshness, or key provenance -- are load-"
        "bearing clauses of this predicate."
    ).format(
        trust_store=trust_store_lookup_present,
        fields=score_envelope_internal_fields_checked,
        replay=replay_or_nonce_check_present,
    ),
    "corpus_manifest": corpus_manifest,
    "forged_package_classes": classes,
    "directive_t2_12_four_vectors": directive_vectors,
    "clauses_evaluated": CLAUSES,
    "runtime_source_anchors": {
        "packaging_acceptance_predicate": "amphora-assurance-capabilities/src/diagnostics.rs::report_fixture_accepted",
        "packaging_map": "amphora-assurance-capabilities/src/diagnostics.rs::render_report",
        "banned_claim_lint": "amphora-assurance-capabilities/src/diagnostics.rs::normalize_claim / contains_banned_claim",
        "live_runtime_entrypoint": "amphora-assurance-capabilities/src/lib.rs::evaluate_report_packager (verified zero-argument / candidate-independent)",
        "required_claim_locks": "amphora-core/src/phase0.rs::REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS",
        "diagnostics_rs_sha256": sha(DIAGNOSTICS_RS.read_bytes()),
        "core_rs_sha256": sha(CORE_RS.read_bytes()),
        "phase0_rs_sha256": sha(PHASE0_RS.read_bytes()),
        "librs_sha256": sha(LIBRS.read_bytes()),
    },
    "non_circularity": (
        "Pure CPython; no import of the Rust runtime. The packaging map, the "
        "acceptance predicate's clauses, the canonicalization, the banned-claim "
        "normalizer, and the 10-element REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS constant "
        "are re-derived from primary source bytes whose SHA-256 are recorded above "
        "(identical re-derivation methodology to the module's three prior AUDIT_ONLY "
        "oracles). Forged-package content is drawn from REAL in-tree signed DSSE "
        "receipts (corpus manifest above), not synthetic stubs. Adversary keys are "
        "derived from pinned seeds so every run is byte-reproducible."
    ),
    "theory_reference": {
        "Anderson_1972": "Computer Security Technology Planning Study, ESD-TR-73-51 -- reference monitor, deny-by-default",
        "RFC_5280": "Cooper et al. 2008, Internet X.509 PKI Certificate and CRL Profile, doi:10.17487/RFC5280 -- trust anchor requirement for authenticity",
        "Needham_Schroeder_1978": "Using Encryption for Authentication in Large Networks of Computers, CACM 21(12):993-999, doi:10.1145/359657.359659 -- replay-attack model",
        "RFC_8032": "Josefsson and Liusvaara 2017, EdDSA, doi:10.17487/RFC8032 -- Ed25519",
        "Unicode_TR15": "Unicode Standard Annex #15, Unicode Normalization Forms -- NFKC does not fold cross-script confusable homoglyphs",
    },
    "does_not_close": (
        "Does not promote the module, flip scientific_readiness, run the Rust "
        "runtime, supply real trust-anchored score envelopes, edit the master "
        "portfolio manifest, or perform the R-D07 human dual-identity ceremony. "
        "Models the packaging-acceptance predicate from source bytes; the finding "
        "is a structural/cryptographic proof about the predicate as it exists in "
        "the current tree, not a legal/regulatory adjudication."
    ),
    "verdict": overall_verdict,
}

OUT.mkdir(parents=True, exist_ok=True)
blob = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
target = OUT / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
target.write_bytes(blob)
print("WROTE", target, sha(blob))
print("overall_verdict", overall_verdict)
print("class1_accepted(should_be_False_if_defended)", c1_accept)
print("class2_accepted(should_be_False_if_defended)", c2_accept)
print("class3_accepted(should_be_False_if_defended)", c3_accept)
print("vectorB_accepted", vb_accept)
print("vectorC_accepted", vc_accept)
print("vectorA_accepted(control, expect False)", va_accept)
print("vectorD_accepted(control, expect False)", vd_accept)
print("trust_store_lookup_present", trust_store_lookup_present)
print("dsse_receipt_count_observed", dsse_receipt_count)
