#!/usr/bin/env python3
"""
amphora-report-packager -- report-fixture-narrative-cross-line-phrase-split-v1 (AUDIT_ONLY)

Attack on the STANDING claim carried by prior receipts for this module:

  * live-runtime-diagnostic-parity-v1 (2026-07-31): report_fixture_accepted's
    C10_narrative_lint clause (contains_banned_claim over payload.narrative)
    genuinely polices banned/overclaim content.
  * report-fixture-title-overclaim-v1 (2026-08-15): found the TITLE field is
    never scanned at all (a field-coverage gap). Orthogonal to this attack,
    which stays entirely inside payload.narrative.
  * report-fixture-narrative-zerowidth-lint-evasion-v1 (2026-08-17): found
    that an invisible Unicode Cf character INSERTED inside a single
    narrative-line word-token defeats the substring check. Also orthogonal:
    that attack stays inside ONE narrative line and needs a hostile Unicode
    character. This attack uses no Unicode tricks at all -- pure ASCII --
    and instead exploits how MULTIPLE lines are iterated.
  * T-12 (2026-08-06): Cyrillic homoglyph substitution (cross-script
    confusable). Character SUBSTITUTION, not this attack's mechanism.

NEW theory / hostile input: report_fixture_accepted checks
    fixture.payload.narrative.iter().any(|line| contains_banned_claim(line))
-- i.e. contains_banned_claim is invoked PER ELEMENT of the narrative Vec,
independently, and the lint never runs over the joined/rendered text. But
render_report() concatenates every narrative line, in order, each followed
by a single '\n', directly into the rendered document body -- with NO
paragraph separator between array elements. So an adversary can write a
banned two-word phrase (e.g. "regulatory compliant") by SPLITTING it across
two consecutive narrative array elements: element N ends with the phrase's
first word, element N+1 begins with the phrase's second word. Neither
element's normalized text contains the full phrase, so contains_banned_claim
returns false for both and report_fixture_accepted's C10_narrative_lint
clause never fires -- yet render_report emits them as two adjacent lines
("...is regulatory\ncompliant for...") which read, to any human viewing the
rendered document, as one continuous overclaiming sentence. This needs no
Unicode tricks, no invisible characters, no homoglyphs, no unscanned field:
every character is plain ASCII, inside the one field the lint DOES inspect,
and the bypass is a structural property of per-element iteration vs.
whole-document scanning, not a character-normalization gap.

Positive/negative controls retained from the live-runtime, title-overclaim,
and zerowidth oracles (signed-known-answer ACCEPT; forged-signature /
envelope-mismatch / stripped-lock / single-line-banned-claim REJECT), PLUS a
same-phrase-single-line control proving the lint DOES catch the identical
banned phrase when it is NOT split across array elements (isolating the
cross-line mechanism, not a broader lint failure).
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
# in render-claim-lock-preservation-v1 G4 and reused by T-12 / title-overclaim-v1 /
# narrative-zerowidth-lint-evasion-v1.
ADVERSARY_SEED_A = hashlib.sha256(
    b"amphora-report-packager-crossline-phrase-split-adversary-key-A-v1"
).digest()
ADVERSARY_SEED_B = hashlib.sha256(
    b"amphora-report-packager-crossline-phrase-split-adversary-key-B-v1"
).digest()
ADVERSARY_SEED_C = hashlib.sha256(
    b"amphora-report-packager-crossline-phrase-split-adversary-key-C-v1"
).digest()
ADVERSARY_SEED_CONTROL = hashlib.sha256(
    b"amphora-report-packager-crossline-phrase-split-adversary-key-control-v1"
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
    UNCHANGED from evidence/audit/live-runtime-diagnostic-parity-v1/,
    report-fixture-title-overclaim-v1/, and
    report-fixture-narrative-zerowidth-lint-evasion-v1/ (all validated
    byte-exact against the live compiled runtime / re-confirmed unchanged).
    In particular note the per-element `.any(|line| ...)` iteration below is
    copied verbatim from src -- THAT iteration shape is the object of this
    attack, not a simplification introduced by this oracle."""
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


def build_fixture_with_narrative_lines(base: dict, seed: bytes, extra_lines) -> dict:
    """A known-answer fixture whose TITLE is clean and whose narrative is the
    baseline line plus extra_lines appended verbatim (in order), self-signed
    by a fresh, deterministic adversary key (key_id self-derives, same
    unpinned-key precondition documented in render-claim-lock-preservation-v1
    G4 and reused by T-12 / title-overclaim-v1 / zerowidth-lint-evasion-v1)."""
    payload = json.loads(json.dumps(base["payload"]))
    payload["narrative"] = list(payload["narrative"]) + list(extra_lines)
    rendered = render_report(payload)
    payload["rendered_document"] = rendered
    payload["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(rendered.encode("utf-8"))
    }
    signature = sign_payload(payload, seed)
    return {"schema": base["schema"], "payload": payload, "signature": signature}


# Three independent cross-line phrase splits, drawn from three different
# banned phrases in the 8-item lexicon, each split at the word boundary
# between the two array elements (no Unicode tricks -- pure ASCII).
SPLIT_A = (
    "Independent evaluation of this coating system confirms it is regulatory",
    "compliant for marine anti-corrosion service under the stated envelope.",
)
SPLIT_B = (
    "The customer-facing summary states the deliverable is procurement",
    "ready for immediate release to the field trial program.",
)
SPLIT_C = (
    "This formulation, per the attached score envelope, is product",
    "qualified for the intended marine coating application.",
)

# Same-phrase-single-line control: identical wording, NOT split across
# array elements, to prove the lint DOES catch it when the full phrase is
# collinear with itself (isolates the cross-line mechanism specifically).
CONTROL_SINGLE_LINE = (
    "Independent evaluation of this coating system confirms it is "
    "regulatory compliant for marine anti-corrosion service under the "
    "stated envelope.",
)


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

    hostile_a = build_fixture_with_narrative_lines(fixture, ADVERSARY_SEED_A, SPLIT_A)
    hostile_b = build_fixture_with_narrative_lines(fixture, ADVERSARY_SEED_B, SPLIT_B)
    hostile_c = build_fixture_with_narrative_lines(fixture, ADVERSARY_SEED_C, SPLIT_C)
    control_single_line = build_fixture_with_narrative_lines(
        fixture, ADVERSARY_SEED_CONTROL, CONTROL_SINGLE_LINE
    )

    # Sanity: neither half-line of each split, alone, trips the lexicon; the
    # concatenation (what a human sees in the rendered document) does.
    for first, second in (SPLIT_A, SPLIT_B, SPLIT_C):
        assert not contains_banned_claim(first), "first half unexpectedly caught alone"
        assert not contains_banned_claim(second), "second half unexpectedly caught alone"
        joined = first + " " + second
        assert contains_banned_claim(joined), "joined halves unexpectedly NOT a banned phrase"
    for line in CONTROL_SINGLE_LINE:
        assert contains_banned_claim(line), "single-line control unexpectedly NOT caught"

    calibration_expected = {
        "signed-known-answer": "ACCEPT",
        "forged-signature": "REJECT",
        "score-envelope-mismatch": "REJECT",
        "stripped-authority-lock": "REJECT",
        "single-line-banned-claim-control": "REJECT",
    }
    calibration_observed = {
        "signed-known-answer": outcome(fixture_accepted(fixture)),
        "forged-signature": outcome(fixture_accepted(forged)),
        "score-envelope-mismatch": outcome(fixture_accepted(envelope_mismatch)),
        "stripped-authority-lock": outcome(fixture_accepted(stripped_lock)),
        "single-line-banned-claim-control": outcome(fixture_accepted(control_single_line)),
    }
    calibration_pass = calibration_expected == calibration_observed

    attack_expected = "REJECT"  # mission.md red-team dossier: overclaim must fail closed
    attack_observed = {
        "crossline-split-A-regulatory-compliant": outcome(fixture_accepted(hostile_a)),
        "crossline-split-B-procurement-ready": outcome(fixture_accepted(hostile_b)),
        "crossline-split-C-product-qualified": outcome(fixture_accepted(hostile_c)),
    }
    attack_refutes_claim = any(v != attack_expected for v in attack_observed.values())
    attack_fires_count = sum(1 for v in attack_observed.values() if v != attack_expected)

    result = {
        "schema": "amphora.report-packager.narrative-crossline-phrase-split-attack.v1",
        "study_id": "report-fixture-narrative-cross-line-phrase-split-v1",
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
            "banned_claim_lint": "amphora-assurance-capabilities/src/diagnostics.rs::report_fixture_accepted / contains_banned_claim",
        },
        "mechanism": (
            "report_fixture_accepted's C10_narrative_lint clause is "
            "`fixture.payload.narrative.iter().any(|line| "
            "contains_banned_claim(line))` -- contains_banned_claim runs "
            "PER ARRAY ELEMENT, independently, never over the joined or "
            "rendered text. render_report() concatenates every narrative "
            "element in order, each terminated by a single newline, directly "
            "into the rendered document body -- there is no paragraph "
            "separator, sentinel, or re-scan step between elements. An "
            "adversary can therefore write any banned two-word phrase by "
            "ending one narrative array element with the phrase's first word "
            "and beginning the NEXT element with its second word: each "
            "element's normalized text lacks the full phrase, so "
            "contains_banned_claim returns false on both, and the `.any()` "
            "over the whole vector is false -- yet render_report emits them "
            "as two immediately adjacent lines that read, to a human viewing "
            "the rendered document, as one continuous overclaiming sentence. "
            "Unlike the zerowidth-lint-evasion-v1 vector (an invisible "
            "Unicode character inserted mid-token, defeating the alphanumeric "
            "sweep inside ONE line), this attack uses zero Unicode tricks -- "
            "every character is plain, visible ASCII -- and the defeated "
            "mechanism is per-element iteration versus whole-document "
            "scanning, not character normalization. Unlike title-overclaim-v1 "
            "(a field the lint never inspects at all), every character of "
            "this attack lives inside payload.narrative, the one field "
            "C10_narrative_lint actually runs over."
        ),
        "calibration": {
            "purpose": (
                "prove this oracle is the SAME implementation validated "
                "byte-exact against the live compiled runtime in "
                "live-runtime-diagnostic-parity-v1 (unmodified "
                "fixture_accepted/render_report/contains_banned_claim), AND "
                "that the identical banned phrase IS caught when written on "
                "a single narrative line rather than split across two -- "
                "isolating the cross-line mechanism as the sole cause of the "
                "bypass, not a general lint failure"
            ),
            "expected": calibration_expected,
            "observed": calibration_observed,
            "calibration_pass": calibration_pass,
        },
        "attack": {
            "description": (
                "three known-answer fixtures, each with a clean title and a "
                "narrative that adds TWO hostile lines: a banned phrase from "
                "the 8-item lexicon split at its internal word boundary "
                "across two consecutive narrative array elements, drawn from "
                "three different phrases; each self-signed with a fresh, "
                "deterministic adversary Ed25519 key"
            ),
            "splits": {
                "A_regulatory_compliant": SPLIT_A,
                "B_procurement_ready": SPLIT_B,
                "C_product_qualified": SPLIT_C,
            },
            "half_lines_trip_banned_claim_lexicon_individually": {
                "A_first": contains_banned_claim(SPLIT_A[0]),
                "A_second": contains_banned_claim(SPLIT_A[1]),
                "B_first": contains_banned_claim(SPLIT_B[0]),
                "B_second": contains_banned_claim(SPLIT_B[1]),
                "C_first": contains_banned_claim(SPLIT_C[0]),
                "C_second": contains_banned_claim(SPLIT_C[1]),
            },
            "joined_halves_ARE_a_banned_phrase": {
                "A": contains_banned_claim(SPLIT_A[0] + " " + SPLIT_A[1]),
                "B": contains_banned_claim(SPLIT_B[0] + " " + SPLIT_B[1]),
                "C": contains_banned_claim(SPLIT_C[0] + " " + SPLIT_C[1]),
            },
            "single_line_control_IS_caught": {
                "regulatory_compliant": contains_banned_claim(CONTROL_SINGLE_LINE[0]),
            },
            "rendered_document_hostile_lines": {
                "A": hostile_a["payload"]["rendered_document"].splitlines()[2:4],
                "B": hostile_b["payload"]["rendered_document"].splitlines()[2:4],
                "C": hostile_c["payload"]["rendered_document"].splitlines()[2:4],
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
            "Does not promote the module, flip scientific_readiness, run the "
            "Rust runtime, supply real trust-anchored score envelopes, edit "
            "the master portfolio manifest, or perform the human dual-"
            "identity ceremony. Models the packaging-acceptance predicate "
            "from source bytes; the finding is a structural proof about the "
            "predicate as it exists in the current tree, not a legal/"
            "regulatory adjudication. Does not certify "
            "signed_report_package_present=true (hardcoded false pending "
            "Phase-1) or claim the production banned_claim_lint_pass gate "
            "(also hardcoded false, not wired to report_fixture_accepted) is "
            "affected."
        ),
        "verdict": "CLAIM_REFUTED" if (calibration_pass and attack_refutes_claim) else "INCONCLUSIVE",
    }
    return result


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=False))
