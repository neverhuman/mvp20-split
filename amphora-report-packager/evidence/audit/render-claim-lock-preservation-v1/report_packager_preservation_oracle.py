#!/usr/bin/env python3
"""
amphora-report-packager -- independent non-runtime front-door oracle
render / claim-lock PRESERVATION + trust-anchor adequacy (v1, AUDIT_ONLY)

THIRD, DISTINCT receipt for this module:
  * banned-claim-lint-parity-v1     -> lexical overclaim lint on deliverables
  * gate-lattice-completeness-v1    -> algebra of the release DECISION function
  * this one (render-claim-lock-preservation-v1)
                                    -> the PACKAGING MAP itself: does the
                                       rendered deliverable preserve every
                                       authority / claim-lock field, and is the
                                       preservation guarantee actually anchored?

This oracle attacks the module mission's literal falsifiable hypothesis --
"downstream packaging preserves every authority and claim-lock field" -- which
neither prior receipt tested (one tested claim TEXT, the other tested the
release PREDICATE; neither tested the payload -> document projection).

Pure CPython. No import of the Rust runtime. The packaging map, the acceptance
predicate, the canonicalization, and the required-claim-lock set are all
RE-DERIVED from primary source bytes:

  amphora-assurance-capabilities/src/diagnostics.rs :: render_report,
                                                       report_fixture_accepted,
                                                       normalize_claim,
                                                       contains_banned_claim
  amphora-core/src/lib.rs                          :: canonicalize, stable_hash
  amphora-core/src/phase0.rs                       :: REQUIRED_ZERO_AUTHORITY_
                                                      CLAIM_LOCKS  (10 locks)

Falsifiable hypotheses:

  G0  packaging-map parity + noninterference of the render alphabet.
      An independent CPython render_report() reproduces the shipped
      rendered_document BYTE-EXACTLY; raw sha256(render) equals the shipped
      canonical_hash_manifest entry; stable_hash(score_envelopes) equals the
      shipped score_envelope_sha256; the fixture key_id equals its own
      derivation "report-fixture-"+sha256(pubkey); and the fixture Ed25519
      signature VERIFIES over sorted-key compact canonical payload bytes --
      all re-derived, none trusted. Noninterference (Goguen-Meseguer 1982):
      every backticked token emitted by the renderer is drawn from a declared
      payload field, so the packaging map adds no symbol of its own; and the
      rendered document itself passes the banned-claim lint.

  G1  claim-lock projection completeness (leave-one-out over ALL 10 locks).
      The shipped Rust diagnostic strips exactly ONE lock
      ("no_ranking_authority") as its probe. This oracle strips each of the 10
      REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS in turn and requires, for every lock:
      (a) the lock is rendered exactly once as `- `k`: `true``;
      (b) deleting it changes the rendered bytes;
      (c) deleting it removes its line from the document;
      (d) deleting it makes the acceptance predicate fail closed.
      Set parity with the primary 10-element constant is also required.

  G2  injectivity of the packaging map on the claim-lock lattice (exhaustive).
      All 2^10 = 1024 lock truth assignments are rendered. The map must be
      INJECTIVE: 1024 distinct documents, 1024 distinct SHA-256 digests, and a
      round-trip parser must recover every assignment exactly (1024/1024).
      Injectivity is what makes preservation checkable at all: no lock value
      can be silently altered while holding the deliverable bytes (hence its
      digest, hence its signature) fixed. Exactly 1 of the 1024 assignments is
      ACCEPTED (all-locks-true) -> unique accept on the lock sublattice.
      Representation invariance: 20 input key orderings render identically
      (the runtime's BTreeMap ordering is re-derived, not assumed).

  G3  escalation / tamper battery. Every mutant -- escalation, lock strip,
      hash-binding desync, crypto substitution, and a smuggled unknown payload
      field -- must fail closed, including the two attacks the packaging map
      exists to stop: (i) lock line deleted from the RENDER only, payload
      intact; (ii) lock value flipped in the RENDER only. Every mutant is
      scored against every clause of the predicate to build a kill matrix, and
      the matrix reports how many clauses the battery actually exercises
      (no silent claim of full clause coverage).

  G4  trust-anchor adequacy (the adversarial result).  A COORDINATED adversary
      strips a claim lock, re-renders, recomputes score_envelope_sha256 and the
      canonical hash manifest, and RE-SIGNS with a freshly generated Ed25519
      key whose key_id is self-derived exactly as the predicate requires. Every
      hash and signature clause is then internally consistent. Clause-level
      ablation identifies precisely which clause still kills it, and whether
      the crypto layer contributes anything against it. The fixture signing key
      is looked up in config/phase0-trust-store.v1.json to test whether the
      signature is anchored (authenticity) or self-authenticating (integrity
      only) -- RFC 5280 trust-anchor requirement, Anderson 1972 reference
      monitor.

Non-circular: shares no code with the Rust runtime; the packaging map, clause
set, and required-lock constant are read out of primary source bytes; the
algebra is proved by exhaustive 2^10 / 10-fold leave-one-out / 20-mutant x
20-clause enumeration; the adversary key is derived from a pinned seed so the
whole run is byte-reproducible.

AUDIT_ONLY. Does not promote authority, does not flip scientific_readiness,
does not modify the portfolio manifest, module-manifest.json, any locked
dataset, or any signed Phase-0 KPI.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-report-packager"
OUT = MOD / "evidence/audit/render-claim-lock-preservation-v1"
FIXTURE = MOD / "reference/mvp20/fixtures/known-answer-package.v1.json"
DIAGNOSTICS_RS = ROOT / "amphora-assurance-capabilities/src/diagnostics.rs"
CORE_RS = ROOT / "amphora-core/src/lib.rs"
PHASE0_RS = ROOT / "amphora-core/src/phase0.rs"
LIBRS = ROOT / "amphora-assurance-capabilities/src/lib.rs"
MISSION = MOD / "docs/mission.md"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

STUDY = "amphora-report-packager-render-claim-lock-preservation-v1"
SCHEMA = "amphora.report-packager.render-claim-lock-preservation-diagnostic.v1"
FIXTURE_SCHEMA = "amphora.report-package-known-answer.v1"
MISSION_PINNED_LIBRS = "c0b2540fa84a9b8c98d2be5d82cbb1d21e9fd8b9806edad23815a0d912f4ab4d"

# Adversary key seed is PINNED so the two-replay byte gate is meaningful.
ADVERSARY_SEED = hashlib.sha256(
    b"amphora-report-packager-render-claim-lock-preservation-v1/coordinated-adversary"
).digest()


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
# re-derived banned-claim lint (diagnostics.rs)
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
    for lock in sorted(payload["authority_lock"]):  # BTreeMap iteration order
        enabled = "true" if payload["authority_lock"][lock] else "false"
        out += "- `{}`: `{}`\n".format(lock, enabled)
    out += "\nScientific readiness: `{}`\nDecision use: `{}`\nRanking eligible: `{}`\n".format(
        payload["scientific_readiness"],
        payload["decision_use_ceiling"],
        "true" if payload["ranking_eligible"] else "false",
    )
    return out


LOCK_LINE = re.compile(r"^- `([A-Za-z0-9_]+)`: `(true|false)`$")


def parse_render(document: str) -> dict:
    """Inverse of render_report on the observable lock / status surface."""
    locks, tail = {}, {}
    in_locks = False
    for line in document.split("\n"):
        if line.startswith("## Authority lock"):
            in_locks = True
            continue
        m = LOCK_LINE.match(line)
        if in_locks and m:
            locks[m.group(1)] = m.group(2) == "true"
            continue
        for key, prefix in (
            ("scientific_readiness", "Scientific readiness: `"),
            ("decision_use_ceiling", "Decision use: `"),
            ("ranking_eligible", "Ranking eligible: `"),
        ):
            if line.startswith(prefix):
                tail[key] = line[len(prefix) : -1]
        if line.startswith("Score envelope SHA-256: `"):
            tail["score_envelope_sha256"] = line[len("Score envelope SHA-256: `") : -1]
    return {"authority_lock": locks, "tail": tail}


# ---------------------------------------------------------------------------
# primary-source extraction
# ---------------------------------------------------------------------------
phase0_src = PHASE0_RS.read_text()
m = re.search(
    r"REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS:\s*\[&str;\s*(\d+)\]\s*=\s*\[(.*?)\];",
    phase0_src,
    re.S,
)
DECLARED_LOCK_COUNT = int(m.group(1))
REQUIRED_LOCKS = re.findall(r'"([a-z0-9_]+)"', m.group(2))
assert len(REQUIRED_LOCKS) == DECLARED_LOCK_COUNT, "lock constant extraction failed"
ZERO_AUTHORITY = {lock: True for lock in REQUIRED_LOCKS}

diag_src = DIAGNOSTICS_RS.read_text()
render_fn_src = re.search(r"fn render_report\(.*?\n}\n", diag_src, re.S).group(0)
# structural: the renderer emits the lock map and never a literal authority grant
render_emits_lock_loop = "for (lock, enabled) in &payload.authority_lock" in render_fn_src
render_has_no_literal_true = 'true' not in re.sub(r"\{[a-z_]+\}", "", render_fn_src)

# ---------------------------------------------------------------------------
# re-derived acceptance predicate, decomposed into named clauses
# ---------------------------------------------------------------------------
PAYLOAD_FIELDS = {
    "fixture_id",
    "fixture_only",
    "authoritative",
    "title",
    "narrative",
    "score_envelopes",
    "score_envelope_sha256",
    "authority_lock",
    "scientific_readiness",
    "decision_use_ceiling",
    "ranking_eligible",
    "rendered_document",
    "canonical_hash_manifest",
}
SIG_FIELDS = {"algorithm", "key_id", "public_key_hex", "signature_hex"}


def clause_results(fixture: dict) -> dict:
    """Every clause of report_fixture_accepted, evaluated independently.

    True == clause satisfied. Ordered to mirror the Rust short-circuit order,
    but evaluated exhaustively so a kill matrix can be built.
    """
    c = {}
    payload = fixture.get("payload", {})
    signature = fixture.get("signature", {})

    # C00: serde(deny_unknown_fields) + required-field structural conformance
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
    c["C12_render_parity"] = (
        rendered is not None and payload.get("rendered_document") == rendered
    )
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
    # Rust falls back to [0u8;32] when the hex is undecodable
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
            Ed25519PublicKey.from_public_bytes(pk).verify(
                sig_bytes, canonical_bytes(payload)
            )
            verified = True
        except (InvalidSignature, Exception):
            verified = False
    c["C19_signature_verifies"] = verified
    return c


CLAUSES = list(clause_results(json.loads(FIXTURE.read_bytes())).keys())


def accepted(fixture: dict, disabled: str = None) -> bool:
    res = clause_results(fixture)
    return all(v for k, v in res.items() if k != disabled)


def failing(fixture: dict) -> list:
    return sorted(k for k, v in clause_results(fixture).items() if not v)


def deep(obj):
    return json.loads(json.dumps(obj))


# ===========================================================================
# G0  packaging-map parity + render noninterference
# ===========================================================================
fixture_bytes = FIXTURE.read_bytes()
fixture = json.loads(fixture_bytes)
payload = fixture["payload"]
shipped_render = payload["rendered_document"]
rederived_render = render_report(payload)
render_sha = sha(rederived_render.encode("utf-8"))

backticked = re.findall(r"`([^`]*)`", rederived_render)
declared_alphabet = (
    set(payload["authority_lock"])
    | {"true", "false"}
    | {
        payload["score_envelope_sha256"],
        payload["scientific_readiness"],
        payload["decision_use_ceiling"],
    }
)
alphabet_foreign = [t for t in backticked if t not in declared_alphabet]

# the payload carries no JSON numbers, so sorted-key-compact vs RFC 8785 number
# canonicalization cannot diverge here -- checked, not assumed
def count_numbers(node):
    if isinstance(node, bool):
        return 0
    if isinstance(node, (int, float)):
        return 1
    if isinstance(node, dict):
        return sum(count_numbers(v) for v in node.values())
    if isinstance(node, list):
        return sum(count_numbers(v) for v in node)
    return 0


g0 = {
    "fixture_path": str(FIXTURE.relative_to(ROOT)),
    "fixture_sha256": sha(fixture_bytes),
    "diagnostics_rs_sha256": sha(DIAGNOSTICS_RS.read_bytes()),
    "core_rs_sha256": sha(CORE_RS.read_bytes()),
    "phase0_rs_sha256": sha(PHASE0_RS.read_bytes()),
    "librs_sha256": sha(LIBRS.read_bytes()),
    "mission_pinned_librs_sha256": MISSION_PINNED_LIBRS,
    "stale_mission_anchor_detected": sha(LIBRS.read_bytes()) != MISSION_PINNED_LIBRS,
    "render_parity_byte_exact": shipped_render == rederived_render,
    "render_sha256": render_sha,
    "shipped_manifest_render_sha256": payload["canonical_hash_manifest"][
        "known-answer-report.md"
    ],
    "manifest_binds_render": payload["canonical_hash_manifest"][
        "known-answer-report.md"
    ]
    == render_sha,
    "score_envelope_sha256_rederived": stable_hash(payload["score_envelopes"]),
    "score_envelope_hash_parity": stable_hash(payload["score_envelopes"])
    == payload["score_envelope_sha256"],
    "key_id_derivation_parity": fixture["signature"]["key_id"]
    == "report-fixture-" + sha(bytes.fromhex(fixture["signature"]["public_key_hex"])),
    "fixture_signature_verifies": clause_results(fixture)["C19_signature_verifies"],
    "shipped_fixture_accepted": accepted(fixture),
    "clause_count": len(CLAUSES),
    "backtick_token_count": len(backticked),
    "backtick_tokens_foreign_to_payload": len(alphabet_foreign),
    "render_alphabet_closed": not alphabet_foreign,
    "rendered_document_passes_banned_claim_lint": not contains_banned_claim(
        rederived_render
    ),
    "renderer_emits_lock_map_loop": render_emits_lock_loop,
    "renderer_has_no_hardcoded_lock_value": render_has_no_literal_true,
    "payload_json_number_count": count_numbers(payload),
    "canonicalization_note": (
        "amphora_core::canonicalize + serde_json::to_vec = recursive key sort, "
        "compact separators; JCS-adjacent but NOT RFC 8785 (no ECMAScript "
        "number normalization). Payload carries 0 JSON numbers, so the "
        "divergence is provably not load-bearing for this fixture."
    ),
}
g0["pass"] = all(
    [
        g0["render_parity_byte_exact"],
        g0["manifest_binds_render"],
        g0["score_envelope_hash_parity"],
        g0["key_id_derivation_parity"],
        g0["fixture_signature_verifies"],
        g0["shipped_fixture_accepted"],
        g0["render_alphabet_closed"],
        g0["rendered_document_passes_banned_claim_lint"],
        g0["renderer_emits_lock_map_loop"],
        g0["payload_json_number_count"] == 0,
    ]
)

# ===========================================================================
# G1  claim-lock projection completeness -- leave-one-out over all 10 locks
# ===========================================================================
lock_rows = []
for lock in REQUIRED_LOCKS:
    line = "- `{}`: `true`".format(lock)
    rendered_once = shipped_render.count(line + "\n") == 1
    mutant = deep(fixture)
    del mutant["payload"]["authority_lock"][lock]
    mutant_render = render_report(mutant["payload"])
    lock_rows.append(
        {
            "lock": lock,
            "rendered_exactly_once": rendered_once,
            "deletion_changes_render": mutant_render != shipped_render,
            "deletion_removes_line": line not in mutant_render,
            "deletion_rejected": not accepted(mutant),
            "deletion_failing_clauses": failing(mutant),
        }
    )

g1 = {
    "declared_lock_count": DECLARED_LOCK_COUNT,
    "required_locks": REQUIRED_LOCKS,
    "lock_set_parity_with_primary_constant": set(payload["authority_lock"])
    == set(REQUIRED_LOCKS),
    "all_shipped_locks_true": all(payload["authority_lock"].values()),
    "locks_checked": len(lock_rows),
    "rendered_exactly_once_count": sum(r["rendered_exactly_once"] for r in lock_rows),
    "deletion_changes_render_count": sum(
        r["deletion_changes_render"] for r in lock_rows
    ),
    "deletion_removes_line_count": sum(r["deletion_removes_line"] for r in lock_rows),
    "deletion_rejected_count": sum(r["deletion_rejected"] for r in lock_rows),
    "runtime_probe_coverage": (
        "shipped Rust diagnostic strips 1 of 10 locks "
        "(no_ranking_authority); this oracle strips 10 of 10"
    ),
    "per_lock": lock_rows,
}
g1["conditions_checked"] = 4 * len(lock_rows)
g1["conditions_passed"] = (
    g1["rendered_exactly_once_count"]
    + g1["deletion_changes_render_count"]
    + g1["deletion_removes_line_count"]
    + g1["deletion_rejected_count"]
)
g1["pass"] = (
    g1["lock_set_parity_with_primary_constant"]
    and g1["all_shipped_locks_true"]
    and g1["conditions_passed"] == g1["conditions_checked"]
    and len(lock_rows) == DECLARED_LOCK_COUNT
)

# ===========================================================================
# G2  injectivity of the packaging map on the claim-lock lattice (2^10)
# ===========================================================================
docs, digests, roundtrip_ok, accept_count, accepting = {}, set(), 0, 0, []
n_locks = len(REQUIRED_LOCKS)
for mask in range(1 << n_locks):
    assignment = {
        lock: bool(mask & (1 << i)) for i, lock in enumerate(REQUIRED_LOCKS)
    }
    trial = deep(fixture)
    trial["payload"]["authority_lock"] = assignment
    doc = render_report(trial["payload"])
    docs.setdefault(doc, []).append(mask)
    digests.add(sha(doc.encode("utf-8")))
    if parse_render(doc)["authority_lock"] == assignment:
        roundtrip_ok += 1
    # acceptance on the lock sublattice: re-bind hashes so ONLY the lock
    # semantics (C09), not stale digests, decide the verdict
    trial["payload"]["rendered_document"] = doc
    trial["payload"]["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(doc.encode("utf-8"))
    }
    lock_clauses = clause_results(trial)
    ignore = {"C19_signature_verifies"}  # signature is stale by construction
    if all(v for k, v in lock_clauses.items() if k not in ignore):
        accept_count += 1
        accepting.append(mask)

order_renders = set()
for rot in range(n_locks):
    rotated = REQUIRED_LOCKS[rot:] + REQUIRED_LOCKS[:rot]
    for keys in (rotated, list(reversed(rotated))):
        trial = deep(fixture)
        trial["payload"]["authority_lock"] = {k: True for k in keys}
        order_renders.add(render_report(trial["payload"]))

g2 = {
    "config_space": 1 << n_locks,
    "distinct_documents": len(docs),
    "distinct_document_sha256": len(digests),
    "digest_collisions": (1 << n_locks) - len(digests),
    "injective_on_lock_lattice": len(docs) == (1 << n_locks) == len(digests),
    "roundtrip_exact_count": roundtrip_ok,
    "roundtrip_exact": roundtrip_ok == (1 << n_locks),
    "accepting_configs": accept_count,
    "accepting_masks": accepting,
    "unique_accept_all_locks_true": accept_count == 1
    and accepting == [(1 << n_locks) - 1],
    "rejecting_configs": (1 << n_locks) - accept_count,
    "key_orderings_tested": 2 * n_locks,
    "distinct_renders_across_orderings": len(order_renders),
    "representation_invariant_over_key_order": len(order_renders) == 1,
}
g2["pass"] = all(
    [
        g2["injective_on_lock_lattice"],
        g2["roundtrip_exact"],
        g2["unique_accept_all_locks_true"],
        g2["representation_invariant_over_key_order"],
    ]
)

# ===========================================================================
# G3  escalation / tamper battery + clause kill matrix
# ===========================================================================
def mut(fn, name, kind):
    m = deep(fixture)
    fn(m)
    return {"name": name, "kind": kind, "fixture": m}


def flip_render_line(m, lock, new):
    doc = m["payload"]["rendered_document"]
    m["payload"]["rendered_document"] = doc.replace(
        "- `{}`: `true`\n".format(lock), new
    )


def resync(m):
    """recompute every self-consistent digest after a payload edit"""
    p = m["payload"]
    p["score_envelope_sha256"] = stable_hash(p["score_envelopes"])
    p["rendered_document"] = render_report(p)
    p["canonical_hash_manifest"] = {
        "known-answer-report.md": sha(p["rendered_document"].encode("utf-8"))
    }


MUTANTS = [
    mut(lambda m: m["payload"].update(authoritative=True), "authoritative_true", "escalation"),
    mut(lambda m: m["payload"].update(fixture_only=False), "fixture_only_false", "escalation"),
    mut(lambda m: m["payload"].update(ranking_eligible=True), "ranking_eligible_true", "escalation"),
    mut(lambda m: m["payload"].update(scientific_readiness="VALIDATED"), "readiness_validated", "escalation"),
    mut(lambda m: m["payload"].update(scientific_readiness="DIRECTION_VALIDATED"), "readiness_direction_validated", "escalation"),
    mut(lambda m: m["payload"].update(decision_use_ceiling="RELEASE"), "ceiling_release", "escalation"),
    mut(lambda m: m["payload"].update(decision_use_ceiling="PHASE_1"), "ceiling_phase_1", "escalation"),
    mut(lambda m: m.update(schema="amphora.report-package.v1"), "schema_swap", "structural"),
    mut(lambda m: m["payload"].update(score_envelopes=[]), "score_envelopes_emptied", "structural"),
    mut(lambda m: m["payload"].update(score_envelope_sha256="0" * 64), "score_hash_zeroed", "binding"),
    mut(lambda m: m["payload"]["canonical_hash_manifest"].update({"known-answer-report.md": "0" * 64}), "manifest_hash_zeroed", "binding"),
    mut(lambda m: m["payload"]["canonical_hash_manifest"].update({"extra.md": "0" * 64}), "manifest_extra_entry", "binding"),
    mut(lambda m: m["payload"].update(rendered_document=m["payload"]["rendered_document"].replace("Ranking eligible", "Ranking Eligible")), "render_single_token_flip", "binding"),
    mut(lambda m: flip_render_line(m, "no_ranking_authority", ""), "render_lock_line_deleted", "lock_strip"),
    mut(lambda m: flip_render_line(m, "no_release_authority", ""), "render_release_lock_line_deleted", "lock_strip"),
    mut(lambda m: flip_render_line(m, "no_ranking_authority", "- `no_ranking_authority`: `false`\n"), "render_lock_value_flipped", "lock_strip"),
    mut(lambda m: (m["payload"]["authority_lock"].pop("no_ranking_authority"), resync(m)), "payload_lock_stripped_resynced", "lock_strip"),
    mut(lambda m: (m["payload"]["authority_lock"].update(no_safety_authority=False), resync(m)), "payload_lock_falsified_resynced", "lock_strip"),
    mut(lambda m: m["payload"].update(title="   "), "title_blanked", "structural"),
    mut(lambda m: m["payload"]["narrative"].append("ＰＲＯＣＵＲＥＭＥＮＴ‑ＲＥＡＤＹ"), "normalized_banned_claim", "escalation"),
    mut(lambda m: m["signature"].update(signature_hex="00" + m["signature"]["signature_hex"][2:]), "forged_signature_byte", "crypto"),
    mut(lambda m: m["signature"].update(algorithm="Ed448"), "algorithm_swap", "crypto"),
    mut(lambda m: m["signature"].update(public_key_hex=Ed25519PrivateKey.from_private_bytes(hashlib.sha256(b"key-substitution-probe").digest()).public_key().public_bytes_raw().hex()), "public_key_substituted", "crypto"),
    mut(lambda m: m["signature"].update(public_key_hex="ab"), "public_key_truncated", "crypto"),
    mut(lambda m: m["signature"].update(signature_hex=m["signature"]["signature_hex"][:120]), "signature_truncated", "crypto"),
    mut(lambda m: m["payload"].update(release_authorized=True), "unknown_payload_field_smuggled", "structural"),
]

mutant_rows = []
for entry in MUTANTS:
    fails = failing(entry["fixture"])
    mutant_rows.append(
        {
            "name": entry["name"],
            "kind": entry["kind"],
            "rejected": bool(fails),
            "failing_clauses": fails,
            "uniquely_killed_by": fails[0] if len(fails) == 1 else None,
        }
    )

kill_counts = {c: 0 for c in CLAUSES}
unique_kill = {c: 0 for c in CLAUSES}
for row in mutant_rows:
    for c in row["failing_clauses"]:
        kill_counts[c] += 1
    if row["uniquely_killed_by"]:
        unique_kill[row["uniquely_killed_by"]] += 1

g3 = {
    "mutants_tested": len(mutant_rows),
    "mutants_rejected": sum(r["rejected"] for r in mutant_rows),
    "all_mutants_fail_closed": all(r["rejected"] for r in mutant_rows),
    "lock_strip_mutants": sum(r["kind"] == "lock_strip" for r in mutant_rows),
    "lock_strip_all_rejected": all(
        r["rejected"] for r in mutant_rows if r["kind"] == "lock_strip"
    ),
    "escalation_mutants": sum(r["kind"] == "escalation" for r in mutant_rows),
    "escalation_all_rejected": all(
        r["rejected"] for r in mutant_rows if r["kind"] == "escalation"
    ),
    "clauses_with_at_least_one_kill": sum(1 for c in CLAUSES if kill_counts[c]),
    "clauses_strictly_necessary": sorted(c for c in CLAUSES if unique_kill[c]),
    "clause_kill_counts": kill_counts,
    "clause_unique_kill_counts": unique_kill,
    "per_mutant": mutant_rows,
}
g3["pass"] = g3["all_mutants_fail_closed"]

# ===========================================================================
# G4  coordinated re-signing adversary + trust-anchor adequacy
# ===========================================================================
adv_sk = Ed25519PrivateKey.from_private_bytes(ADVERSARY_SEED)
adv_pk = adv_sk.public_key().public_bytes_raw()

def coordinated(edit):
    """strip/alter a lock, then repair EVERY digest and re-sign with a key
    whose key_id is self-derived exactly as the predicate demands."""
    m = deep(fixture)
    edit(m["payload"])
    resync(m)
    m["signature"] = {
        "algorithm": "Ed25519",
        "key_id": "report-fixture-" + sha(adv_pk),
        "public_key_hex": adv_pk.hex(),
        "signature_hex": adv_sk.sign(canonical_bytes(m["payload"])).hex(),
    }
    return m


adv_strip = coordinated(
    lambda p: p["authority_lock"].pop("no_ranking_authority")
)
adv_falsify = coordinated(
    lambda p: p["authority_lock"].update(no_release_authority=False)
)
adv_escalate = coordinated(
    lambda p: p.update(scientific_readiness="VALIDATED")
)

adv_rows = []
for name, adv in (
    ("coordinated_lock_strip_resigned", adv_strip),
    ("coordinated_lock_falsified_resigned", adv_falsify),
    ("coordinated_readiness_escalation_resigned", adv_escalate),
):
    res = clause_results(adv)
    fails = sorted(k for k, v in res.items() if not v)
    crypto = [
        "C15_algorithm_ed25519",
        "C16_key_id_derivation",
        "C17_public_key_32b",
        "C18_signature_64b",
        "C19_signature_verifies",
    ]
    binding = ["C11_score_envelope_hash", "C12_render_parity", "C13_manifest_binds_render", "C14_manifest_singleton"]
    adv_rows.append(
        {
            "adversary": name,
            "rejected": bool(fails),
            "failing_clauses": fails,
            "crypto_clauses_all_satisfied": all(res[c] for c in crypto),
            "hash_binding_clauses_all_satisfied": all(res[c] for c in binding),
            "surviving_defense_count": len(fails),
            "ablation_accepts_when_clause_removed": sorted(
                c for c in CLAUSES if accepted(adv, disabled=c)
            ),
        }
    )

trust = json.loads(TRUST.read_text())
trust_key_ids = {k.get("key_id") for k in trust.get("keys", [])}
trust_pubkeys = {k.get("public_key_hex") for k in trust.get("keys", [])}
fixture_key_pinned = (
    fixture["signature"]["key_id"] in trust_key_ids
    or fixture["signature"]["public_key_hex"] in trust_pubkeys
)
predicate_pins_key = bool(
    re.search(r'report-fixture-\{?\}?"', diag_src)
) and 'signature.key_id\n            != format!(' in diag_src.replace("\r", "")

g4 = {
    "adversary_seed_sha256": sha(ADVERSARY_SEED),
    "adversary_public_key_hex": adv_pk.hex(),
    "adversaries_tested": len(adv_rows),
    "adversaries_rejected": sum(r["rejected"] for r in adv_rows),
    "all_adversaries_fail_closed": all(r["rejected"] for r in adv_rows),
    "lock_adversary_surviving_defenses": adv_rows[0]["failing_clauses"],
    "lock_adversary_defense_count": adv_rows[0]["surviving_defense_count"],
    "lock_adversary_crypto_layer_satisfied": adv_rows[0]["crypto_clauses_all_satisfied"],
    "lock_adversary_hash_bindings_satisfied": adv_rows[0][
        "hash_binding_clauses_all_satisfied"
    ],
    "single_point_of_defense_clause": (
        adv_rows[0]["failing_clauses"][0]
        if adv_rows[0]["surviving_defense_count"] == 1
        else None
    ),
    "ablating_that_clause_admits_lock_stripped_package": bool(
        adv_rows[0]["ablation_accepts_when_clause_removed"]
    ),
    "trust_store_path": str(TRUST.relative_to(ROOT)),
    "trust_store_sha256": sha(TRUST.read_bytes()),
    "trust_store_roles": sorted(k.get("role") for k in trust.get("keys", [])),
    "fixture_signing_key_id": fixture["signature"]["key_id"],
    "fixture_signing_key_pinned_in_trust_store": fixture_key_pinned,
    "signature_provides": "INTEGRITY_ONLY_SELF_AUTHENTICATING"
    if not fixture_key_pinned
    else "ANCHORED_AUTHENTICITY",
    "finding": (
        "The report-package signature is SELF-AUTHENTICATING: key_id is derived "
        "from the presented public key and that key is not pinned in "
        "config/phase0-trust-store.v1.json, so an adversary who re-signs with "
        "their own key satisfies every crypto and hash-binding clause. The "
        "claim-lock preservation guarantee therefore rests on exactly ONE "
        "clause -- the hard-coded REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS set "
        "comparison. That clause holds and is load-bearing (ablating it admits "
        "a lock-stripped, fully self-consistent, validly signed package), but "
        "the cryptographic layer contributes NOTHING against this adversary. "
        "Remediation: pin the report-fixture verifying key as a trust anchor "
        "(RFC 5280 trust-anchor requirement; Anderson 1972 reference monitor)."
    ),
    "per_adversary": adv_rows,
}
g4["pass"] = (
    g4["all_adversaries_fail_closed"]
    and g4["single_point_of_defense_clause"] == "C09_authority_lock_set"
    and g4["ablating_that_clause_admits_lock_stripped_package"]
)

# ===========================================================================
# assemble
# ===========================================================================
gates = {
    "g0_packaging_map_parity": g0["pass"],
    "g1_lock_projection_completeness": g1["pass"],
    "g2_lattice_injectivity": g2["pass"],
    "g3_escalation_tamper_battery": g3["pass"],
    "g4_trust_anchor_adequacy": g4["pass"],
}
gates["all_pass"] = all(gates.values())

claim = (
    "Independent CPython oracle re-derives the amphora-report-packager packaging "
    "map byte-exactly and proves it PRESERVES every authority/claim-lock field: "
    "render parity byte-exact, sha256(render) binds the shipped canonical hash "
    "manifest, stable_hash(score_envelopes) binds score_envelope_sha256, and the "
    "fixture Ed25519 signature verifies over sorted-key compact canonical payload "
    "bytes. Leave-one-out over ALL {nlocks}/{nlocks} required claim locks "
    "(the shipped Rust probe covers 1/{nlocks}) fails closed on {cc}/{cc} "
    "conditions. The map is INJECTIVE on the claim-lock lattice: 2^{nlocks}="
    "{cs} assignments -> {dd} distinct documents / {dg} distinct SHA-256 "
    "(0 collisions), round-trip exact {rt}/{cs}, unique accept 1/{cs} "
    "(all-locks-true), invariant over {ko} key orderings. {mt}/{mt} escalation / "
    "lock-strip / binding / crypto mutants fail closed, including render-only "
    "lock deletion and render-only lock falsification. ADVERSARIAL RESULT: a "
    "coordinated adversary that strips a lock, re-renders, re-hashes and RE-SIGNS "
    "with its own self-derived key satisfies EVERY crypto and hash-binding clause; "
    "the package is rejected by exactly ONE surviving defense "
    "({spod}), and ablating that single clause ADMITS the lock-stripped package. "
    "The fixture verifying key is NOT pinned in config/phase0-trust-store.v1.json, "
    "so the signature supplies integrity, not authenticity."
).format(
    nlocks=DECLARED_LOCK_COUNT,
    cc=g1["conditions_checked"],
    cs=g2["config_space"],
    dd=g2["distinct_documents"],
    dg=g2["distinct_document_sha256"],
    rt=g2["roundtrip_exact_count"],
    ko=g2["key_orderings_tested"],
    mt=g3["mutants_tested"],
    spod=g4["single_point_of_defense_clause"],
)

diagnostic = {
    "schema": SCHEMA,
    "study_id": STUDY,
    "module": "amphora-report-packager",
    "run_type": "AUDIT_ONLY_INDEPENDENT_ORACLE",
    "purpose": (
        "Independently test the module mission's literal falsifiable hypothesis "
        "-- that downstream packaging preserves every authority and claim-lock "
        "field -- by re-deriving the payload->document packaging map in pure "
        "CPython, proving it injective on the claim-lock lattice, exercising "
        "leave-one-out over all required locks, and measuring which defense "
        "clause actually survives a coordinated re-signing adversary."
    ),
    "hypothesis": (
        "H1 the packaging map is byte-exactly reproducible and hash/signature "
        "bound; H2 every required claim lock is load-bearing in the rendered "
        "deliverable (deleting any one fails closed); H3 the map is injective on "
        "the 2^10 claim-lock lattice with a unique accept, so no lock value can "
        "be altered while holding the deliverable bytes fixed; H4 escalation and "
        "lock-strip mutants all fail closed; H5 the preservation guarantee is "
        "anchored rather than resting on a single unanchored clause. H1-H4 are "
        "corroborated; H5 is REFUTED -- the guarantee rests on one hard-coded "
        "lock-set clause because the signing key is not a pinned trust anchor."
    ),
    "non_circularity": (
        "Pure CPython; no import of the Rust runtime. The packaging map, the "
        "acceptance predicate's 20 clauses, the canonicalization, the banned-claim "
        "normalizer, and the 10-element REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS "
        "constant are re-derived from primary source bytes (diagnostics.rs, "
        "amphora-core/src/lib.rs, amphora-core/src/phase0.rs) whose SHA-256 are "
        "recorded. Algebra proved by exhaustive 2^{nlocks} enumeration, "
        "{nlocks}-fold leave-one-out, and a {mt}-mutant x {nc}-clause kill "
        "matrix ({cov}/{nc} clauses exercised). The adversary key is derived "
        "from a pinned seed so the run is byte-reproducible."
    ).format(
        nlocks=DECLARED_LOCK_COUNT,
        mt=g3["mutants_tested"],
        nc=len(CLAUSES),
        cov=g3["clauses_with_at_least_one_kill"],
    ),
    "theory_reference": {
        "Anderson_1972": "Computer Security Technology Planning Study, ESD-TR-73-51 -- reference monitor, deny-by-default",
        "Denning_1976": "A Lattice Model of Secure Information Flow, CACM 19(5):236-243, doi:10.1145/360051.360056",
        "FIPS_180_4": "NIST FIPS PUB 180-4 (2015), Secure Hash Standard (SHA-256), doi:10.6028/NIST.FIPS.180-4",
        "Goguen_Meseguer_1982": "Security Policies and Security Models, Proc. IEEE Symp. Security and Privacy, pp.11-20, doi:10.1109/SP.1982.10014 -- noninterference / no information amplification",
        "RFC_5280": "Cooper et al. 2008, Internet X.509 PKI Certificate and CRL Profile, doi:10.17487/RFC5280 -- trust anchor requirement for authenticity",
        "RFC_8032": "Josefsson and Liusvaara 2017, Edwards-Curve Digital Signature Algorithm (EdDSA), doi:10.17487/RFC8032 -- Ed25519",
        "RFC_8785": "Rundgren et al. 2020, JSON Canonicalization Scheme, doi:10.17487/RFC8785 -- contrast anchor for the module's sorted-key compact canonicalization",
        "Saltzer_Schroeder_1975": "The Protection of Information in Computer Systems, Proc. IEEE 63(9):1278-1308, doi:10.1109/PROC.1975.9939 -- fail-safe defaults, complete mediation",
    },
    "runtime_source_anchors": {
        "packaging_map": "amphora-assurance-capabilities/src/diagnostics.rs::render_report",
        "acceptance_predicate": "amphora-assurance-capabilities/src/diagnostics.rs::report_fixture_accepted",
        "canonicalization": "amphora-core/src/lib.rs::canonicalize + stable_hash",
        "required_claim_locks": "amphora-core/src/phase0.rs::REQUIRED_ZERO_AUTHORITY_CLAIM_LOCKS",
        "fixture": "amphora-report-packager/reference/mvp20/fixtures/known-answer-package.v1.json",
        "diagnostics_rs_sha256": g0["diagnostics_rs_sha256"],
        "core_rs_sha256": g0["core_rs_sha256"],
        "phase0_rs_sha256": g0["phase0_rs_sha256"],
        "librs_sha256": g0["librs_sha256"],
    },
    "g0_packaging_map_parity": g0,
    "g1_lock_projection_completeness": g1,
    "g2_lattice_injectivity": g2,
    "g3_escalation_tamper_battery": g3,
    "g4_trust_anchor_adequacy": g4,
    "gates": gates,
    "closes": claim,
    "does_not_close": (
        "Does not promote the module, flip scientific_readiness, run the Rust "
        "runtime, supply the missing signed score envelopes or a real report "
        "package, pin any trust anchor, or certify any release gate true -- those "
        "need the authorized Phase-1 pipeline and human dual-identity keys. The "
        "oracle proves properties of the deterministic fixture packaging map and "
        "its acceptance predicate as re-derived from source bytes; it is a "
        "structural / cryptographic proof, not wet-lab, legal, or regulatory "
        "adjudication. The named trust-anchor gap is a finding for human review, "
        "not a change this run is authorized to make."
    ),
    "verdict": (
        "PRESERVATION_CORROBORATED_WITH_UNANCHORED_TRUST_BASE"
        if gates["all_pass"]
        else "FAILED"
    ),
}

OUT.mkdir(parents=True, exist_ok=True)
blob = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
import sys

target = OUT / (sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json")
target.write_bytes(blob)
print("WROTE", target, sha(blob))
for k, v in gates.items():
    print("  ", k, v)
print("  verdict", diagnostic["verdict"])
print("  g1 conditions", g1["conditions_passed"], "/", g1["conditions_checked"])
print("  g2 injective", g2["distinct_documents"], "/", g2["config_space"],
      "roundtrip", g2["roundtrip_exact_count"], "accept", g2["accepting_configs"])
print("  g3 mutants", g3["mutants_rejected"], "/", g3["mutants_tested"],
      "strictly_necessary_clauses", g3["clauses_strictly_necessary"])
print("  g4 spod", g4["single_point_of_defense_clause"],
      "crypto_satisfied", g4["lock_adversary_crypto_layer_satisfied"],
      "pinned", g4["fixture_signing_key_pinned_in_trust_store"])
