#!/usr/bin/env python3
"""
amphora-report-packager -- report-fixture-narrative-zerowidth-lint-evasion-v1 (AUDIT_ONLY)

Attack on the STANDING claim carried by four prior receipts for this module:

  * live-runtime-diagnostic-parity-v1 (2026-07-31): "real NFKC fullwidth
    banned-claim rejection" -- report_fixture_accepted's C10_narrative_lint
    clause (contains_banned_claim over payload.narrative) genuinely polices
    banned/overclaim content.
  * report-fixture-title-overclaim-v1 (2026-08-15): found title never
    scanned at all (a FIELD-COVERAGE gap). That gap is orthogonal to this
    attack, which targets the NARRATIVE field -- the one field the lint
    DOES run over -- and asks whether the normalizer itself can be defeated
    while staying inside that field.
  * T-12 (2026-08-06, directive T2-12 vector c): Cyrillic homoglyph
    substitution ("procurement rеady") refuted the lint via a
    CROSS-SCRIPT CONFUSABLE character (NFKC does not fold cross-script
    confusables -- Unicode TR39). That is a different mechanism from this
    attack.

NEW theory / hostile input: normalize_claim() (diagnostics.rs) maps every
character that is NOT alphanumeric -- including invisible Unicode "Format"
(General Category Cf) characters such as ZERO WIDTH SPACE (U+200B), ZERO
WIDTH NON-JOINER (U+200C), and ZERO WIDTH JOINER (U+200D) -- to a literal
space, then collapses runs of whitespace with split_whitespace().join(" ").
NFKC normalization (Unicode TR15) does NOT strip or decompose these Cf
characters; they survive nfkc() as themselves. So inserting exactly one
invisible Cf character INSIDE a single-word token of a banned phrase (not
at a position that is already a word boundary) splits that token into two
substrings separated by a normalized space, which breaks the literal
phrase.contains(normalized) substring check used by contains_banned_claim
-- even though the phrase is 100% legible, copy-pasteable, and renders
character-for-character identically to a human reader (these Cf characters
have zero visible glyph). Unlike the homoglyph vector, no character is
SUBSTITUTED -- every visible letter of the banned phrase is present and
correct; a character is merely INSERTED where it cannot be seen. Unlike the
title-overclaim vector, the banned claim stays inside payload.narrative,
the one field report_fixture_accepted's C10_narrative_lint clause actually
inspects.

Positive/negative controls retained from the live-runtime and
title-overclaim oracles (signed-known-answer ACCEPT, forged-signature /
envelope-mismatch / stripped-lock / fullwidth-homoglyph-narrative REJECT),
PLUS a same-text-without-the-invisible-character control proving the lint
DOES catch the identical banned phrase once the Cf character is removed
(isolating the invisible-character mechanism, not a broader lint failure).
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

# Deterministic adversary keys (fixed seeds => byte-stable two-replay gate).
# NOT the phase0 evaluator/reviewer key; models a coordinated adversary who
# controls their own Ed25519 keypair -- same precondition already documented
# in render-claim-lock-preservation-v1 G4 and reused by T-12 / title-overclaim-v1.
ADVERSARY_SEED_A = hashlib.sha256(
    b"amphora-report-packager-zerowidth-lint-evasion-adversary-key-A-v1"
).digest()
ADVERSARY_SEED_B = hashlib.sha256(
    b"amphora-report-packager-zerowidth-lint-evasion-adversary-key-B-v1"
).digest()
ADVERSARY_SEED_C = hashlib.sha256(
    b"amphora-report-packager-zerowidth-lint-evasion-adversary-key-C-v1"
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
    """Byte-faithful re-derivation of diagnostics.rs::normalize_claim."""
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
    UNCHANGED from evidence/audit/live-runtime-diagnostic-parity-v1/ and
    evidence/audit/report-fixture-title-overclaim-v1/ (both validated
    byte-exact against the live compiled runtime / re-confirmed unchanged)."""
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


def build_fixture_with_narrative_line(base: dict, seed: bytes, narrative_line: str) -> dict:
    """A known-answer fixture whose TITLE is clean but whose NARRATIVE
    contains one hostile line (the rest of the baseline narrative is kept
    intact), self-signed by a fresh, deterministic adversary key (key_id
    self-derives, same unpinned-key precondition documented in
    render-claim-lock-preservation-v1 G4 and reused by T-12 / title-overclaim-v1)."""
    payload = json.loads(json.dumps(base["payload"]))
    payload["narrative"] = list(payload["narrative"]) + [narrative_line]
    rendered = render_report(payload)
    payload["rendered_document"] = rendered
    payload["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(rendered.encode("utf-8"))
    }
    signature = sign_payload(payload, seed)
    return {"schema": base["schema"], "payload": payload, "signature": signature}


# Three independent single-word-token splits, one invisible Cf character each,
# drawn from three DIFFERENT banned phrases and THREE DIFFERENT Cf characters,
# to show this is a systemic property of the normalizer, not a one-off string.
ZWSP = "​"  # ZERO WIDTH SPACE
ZWNJ = "‌"  # ZERO WIDTH NON-JOINER
ZWJ = "‍"   # ZERO WIDTH JOINER

HOSTILE_LINE_A = "This deliverable is pro" + ZWSP + "curement ready for immediate release."
HOSTILE_LINE_B = "The formulation described herein is pat" + ZWNJ + "entable subject matter."
HOSTILE_LINE_C = "This coating is product qual" + ZWJ + "ified for marine service."

CLEAN_ECHO_LINE_A = HOSTILE_LINE_A.replace(ZWSP, "")
CLEAN_ECHO_LINE_B = HOSTILE_LINE_B.replace(ZWNJ, "")
CLEAN_ECHO_LINE_C = HOSTILE_LINE_C.replace(ZWJ, "")


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
    banned_claim_narrative_fullwidth = json.loads(fixture_bytes)
    banned_claim_narrative_fullwidth["payload"]["narrative"].append(
        "ＰＲＯＣＵＲＥＭＥＮＴ"
        "‑ＲＥＡＤＹ"
    )

    hostile_a = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_A, HOSTILE_LINE_A)
    hostile_b = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_B, HOSTILE_LINE_B)
    hostile_c = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_C, HOSTILE_LINE_C)
    clean_echo_a = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_A, CLEAN_ECHO_LINE_A)
    clean_echo_b = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_B, CLEAN_ECHO_LINE_B)
    clean_echo_c = build_fixture_with_narrative_line(fixture, ADVERSARY_SEED_C, CLEAN_ECHO_LINE_C)

    for line in (HOSTILE_LINE_A, HOSTILE_LINE_B, HOSTILE_LINE_C):
        assert not contains_banned_claim(line), "hostile line unexpectedly caught pre-fixture"
    for line in (CLEAN_ECHO_LINE_A, CLEAN_ECHO_LINE_B, CLEAN_ECHO_LINE_C):
        assert contains_banned_claim(line), "clean-echo control unexpectedly NOT caught"

    calibration_expected = {
        "signed-known-answer": "ACCEPT",
        "forged-signature": "REJECT",
        "score-envelope-mismatch": "REJECT",
        "stripped-authority-lock": "REJECT",
        "normalized-banned-claim-narrative-fullwidth": "REJECT",
        "clean-echo-narrative-A-procurement-ready": "REJECT",
        "clean-echo-narrative-B-patentable": "REJECT",
        "clean-echo-narrative-C-product-qualified": "REJECT",
    }
    calibration_observed = {
        "signed-known-answer": outcome(fixture_accepted(fixture)),
        "forged-signature": outcome(fixture_accepted(forged)),
        "score-envelope-mismatch": outcome(fixture_accepted(envelope_mismatch)),
        "stripped-authority-lock": outcome(fixture_accepted(stripped_lock)),
        "normalized-banned-claim-narrative-fullwidth": outcome(
            fixture_accepted(banned_claim_narrative_fullwidth)
        ),
        "clean-echo-narrative-A-procurement-ready": outcome(fixture_accepted(clean_echo_a)),
        "clean-echo-narrative-B-patentable": outcome(fixture_accepted(clean_echo_b)),
        "clean-echo-narrative-C-product-qualified": outcome(fixture_accepted(clean_echo_c)),
    }
    calibration_pass = calibration_expected == calibration_observed

    attack_expected = "REJECT"  # mission.md red-team dossier: overclaim must fail closed
    attack_observed = {
        "invisible-token-split-narrative-A-procurement-ready-ZWSP": outcome(
            fixture_accepted(hostile_a)
        ),
        "invisible-token-split-narrative-B-patentable-ZWNJ": outcome(
            fixture_accepted(hostile_b)
        ),
        "invisible-token-split-narrative-C-product-qualified-ZWJ": outcome(
            fixture_accepted(hostile_c)
        ),
    }
    attack_refutes_claim = any(v != attack_expected for v in attack_observed.values())
    attack_fires_count = sum(1 for v in attack_observed.values() if v != attack_expected)

    result = {
        "schema": "amphora.report-packager.narrative-zerowidth-lint-evasion-attack.v1",
        "study_id": "report-fixture-narrative-zerowidth-lint-evasion-v1",
        "module_id": MODULE,
        "authority": "AUDIT_ONLY",
        "claim_under_attack": (
            "amphora-report-packager/evidence/audit/live-runtime-diagnostic-parity-v1/"
            "live-runtime-diagnostic-parity-receipt.v1.dsse.json :: "
            "g1_outcome_labels ('real NFKC fullwidth banned-claim rejection') AND "
            "amphora-report-packager/evidence/audit/banned-claim-lint-parity-v1 "
            "(banned-claim lint genuinely polices overclaim content via "
            "normalize_claim/contains_banned_claim) AND docs/mission.md red-team "
            "dossier clause 'regulatory, supplier, procurement, qualification, or "
            "release overclaim. Every such case must fail closed or remain an "
            "explicit evidence gap.'"
        ),
        "refutation_criterion_verbatim": "Any prohibited claim, legacy claim, or quarantine bypass reaches a packaged report.",
        "runtime_source_anchors": {
            "assurance_diagnostics_rs_sha256_today": diagnostics_rs_sha256,
            "assurance_diagnostics_rs_sha256_prior_receipt": prior_diagnostics_rs_sha256,
            "runtime_unchanged_since_prior_live_validation": runtime_unchanged_since_prior_live_validation,
            "fixture_path": FIXTURE_PATH_REL,
            "fixture_sha256": sha(fixture_bytes),
            "banned_claim_lint": "amphora-assurance-capabilities/src/diagnostics.rs::normalize_claim / contains_banned_claim",
        },
        "mechanism": (
            "normalize_claim() maps every non-alphanumeric character -- including "
            "invisible Unicode General-Category-Cf 'Format' characters such as "
            "U+200B ZERO WIDTH SPACE, U+200C ZERO WIDTH NON-JOINER, and U+200D "
            "ZERO WIDTH JOINER -- to a literal space, then collapses whitespace "
            "runs. NFKC normalization (Unicode TR15) does not strip or decompose "
            "these Cf characters. Inserting exactly one such character inside a "
            "single-word token of a banned phrase (not already at a word "
            "boundary) splits that token into two space-separated substrings, "
            "defeating the literal `normalized.contains(banned_phrase)` check, "
            "while the text remains 100%% visually and semantically identical to "
            "the banned phrase to any human or copy-paste reader (Cf characters "
            "render with zero width / no glyph)."
        ),
        "calibration": {
            "purpose": (
                "prove this oracle is the SAME implementation validated byte-exact "
                "against the live compiled runtime in live-runtime-diagnostic-parity-v1 "
                "(unmodified fixture_accepted/render_report/contains_banned_claim), "
                "AND that the identical banned phrases (with the invisible character "
                "removed) ARE caught -- isolating the invisible-character mechanism "
                "as the sole cause of the bypass, not a general lint weakness"
            ),
            "expected": calibration_expected,
            "observed": calibration_observed,
            "calibration_pass": calibration_pass,
        },
        "attack": {
            "description": (
                "three known-answer fixtures, each with a clean title and a "
                "narrative that adds ONE hostile line: a banned phrase from the "
                "8-item lexicon with a single invisible Cf character inserted "
                "inside one word-token (procurement/patentable/qualified), drawn "
                "from three different phrases and three different Cf characters; "
                "each self-signed with a fresh, deterministic adversary Ed25519 key"
            ),
            "hostile_lines": {
                "A_procurement_ready_ZWSP": HOSTILE_LINE_A,
                "B_patentable_ZWNJ": HOSTILE_LINE_B,
                "C_product_qualified_ZWJ": HOSTILE_LINE_C,
            },
            "hostile_lines_trip_banned_claim_lexicon_pre_normalization_check": {
                "A": contains_banned_claim(HOSTILE_LINE_A),
                "B": contains_banned_claim(HOSTILE_LINE_B),
                "C": contains_banned_claim(HOSTILE_LINE_C),
            },
            "clean_echo_controls_ARE_caught": {
                "A": contains_banned_claim(CLEAN_ECHO_LINE_A),
                "B": contains_banned_claim(CLEAN_ECHO_LINE_B),
                "C": contains_banned_claim(CLEAN_ECHO_LINE_C),
            },
            "rendered_document_first_narrative_line": {
                "A": hostile_a["payload"]["rendered_document"].splitlines()[1]
                if len(hostile_a["payload"]["rendered_document"].splitlines()) > 1
                else None,
            },
            "expected_per_mission_red_team_dossier": attack_expected,
            "observed": attack_observed,
            "attack_fires_count_of_3": attack_fires_count,
            "attack_refutes_claim": attack_refutes_claim,
            "hostile_fixtures": {
                "A": hostile_a,
                "B": hostile_b,
                "C": hostile_c,
            },
        },
        "does_not_close": (
            "Does not promote the module, flip scientific_readiness, run the Rust "
            "runtime, supply real trust-anchored score envelopes, edit the master "
            "portfolio manifest, or perform the R-D07 human dual-identity ceremony. "
            "Models the packaging-acceptance predicate from source bytes; the "
            "finding is a structural proof about the predicate/normalizer as it "
            "exists in the current tree, not a legal/regulatory adjudication. Does "
            "not certify signed_report_package_present=true (hardcoded false "
            "pending Phase-1) or claim the production banned_claim_lint_pass gate "
            "(also hardcoded false, not wired to report_fixture_accepted) is "
            "affected."
        ),
        "verdict": "CLAIM_REFUTED" if (calibration_pass and attack_refutes_claim) else "INCONCLUSIVE",
    }
    return result


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=False))
