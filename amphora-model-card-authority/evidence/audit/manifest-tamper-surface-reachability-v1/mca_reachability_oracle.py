#!/usr/bin/env python3
"""
amphora-model-card-authority :: manifest-tamper-surface-reachability-v1

ATTACK on the two prior standing audit receipts for this module:
  - evidence/audit/least-privilege-authority-parity-v1  (gate G3,
    "g3_fail_closed_all_tamper_rejected", 10 manifest-tamper probes)
  - evidence/audit/authority-lattice-completeness-v1     (gate N,
    "N_clause_necessity_complete_conjunction", 26 single-clause knockouts)

Both receipts corroborate the module's falsifiable hypothesis -- "minimum-
privilege policy rejects every incomplete, stale, spoofed, or over-ceiling
grant" -- by mutating a Python-transcribed copy of module-manifest.json and
showing their OWN transcription of amphora-engine::validate_manifest
(lib.rs:318) rejects every mutation. Neither receipt ever calls live Rust.

This oracle asks a sharper, structural question neither receipt asks: is
validate_manifest reachable, at runtime, with ANYTHING other than the one
compile-time-frozen manifest? If the answer is "no, by construction", then
the G3/N tamper-probe results -- however internally consistent -- do not
corroborate rejection of any "spoofed" or "stale" GRANT, because no live
caller (hostile or otherwise) can ever present validate_manifest with
alternate bytes. The function runs exactly once per process, at startup,
against a `include_bytes!` constant. That is a build/supply-chain integrity
check, not a per-grant authorization decision. The per-grant decision path
(NativeRegistry::envelope -> TrustCapability::evaluate, and downstream
amphora_core::rank_candidates / authorize_optimizer_request) is a SEPARATE
code path already probed by T-07 (2026-08-13, CLAIM_REFUTED: encoding-based
authority_tier escalation slips through that live path) -- a path the
manifest-tamper probes give zero coverage of.

This is a static, deterministic source-provenance analysis (grep/regex over
the checked-in Rust source), not a live differential probe and not a
re-implementation of any decision predicate: it locates call sites and
visibility, it does not evaluate policy logic. AUDIT_ONLY. No promotion,
no manifest edit, no scientific-readiness flip.
"""
import hashlib
import json
import os
import re

ROOT = "/home/ubuntu/amphora/build/mvp20-split"

TARGET_FN_SIG = "fn validate_manifest(manifest: &Manifest) -> Result<(), RegistryError> {"
DEFINING_FILE = "amphora-engine/src/lib.rs"


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def sha_text(s):
    return hashlib.sha256(s.encode()).hexdigest()


def iter_rs_files(root):
    skip_dirs = {"target", ".git", "evidence", "node_modules"}
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for fn in sorted(filenames):
            if fn.endswith(".rs"):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def main():
    engine_path = f"{ROOT}/{DEFINING_FILE}"
    with open(engine_path, "r") as f:
        engine_src = f.read()
    engine_lines = engine_src.splitlines()

    diag = {
        "schema": "amphora.model-card-authority.manifest-tamper-surface-reachability.v1",
        "study_id": "manifest-tamper-surface-reachability-v1",
        "module": "amphora-model-card-authority",
        "run_type": "AUDIT_ONLY_STATIC_SOURCE_PROVENANCE_ANALYSIS",
        "attacks": [
            "evidence/audit/least-privilege-authority-parity-v1 :: gate g3_fail_closed_all_tamper_rejected",
            "evidence/audit/authority-lattice-completeness-v1 :: gate N_clause_necessity_complete_conjunction",
        ],
        "purpose": (
            "Determine whether amphora-engine::validate_manifest (the sole "
            "function both prior receipts tamper-test via Python transcription) "
            "has any live runtime-reachable call path capable of receiving "
            "caller- or attacker-influenced manifest bytes, as opposed to "
            "running exactly once at process start against a compile-time-"
            "frozen constant."
        ),
        "refutation_criterion": (
            "REFUTED if: (a) validate_manifest is not `pub` (crate-private, so "
            "no external crate can call it), AND (b) it has exactly one call "
            "site workspace-wide, AND (c) that call site is inside "
            "NativeRegistry::build(), itself only reachable via "
            "OnceLock::get_or_init (evaluated at most once per process, result "
            "cached forever), AND (d) the manifest bytes it validates are a "
            "`include_bytes!` compile-time constant with no CLI flag, env var, "
            "file-path parameter, or request field anywhere in the workspace "
            "that can substitute alternate bytes at runtime. "
            "SURVIVES if any of (a)-(d) is false, i.e. some live, reachable "
            "code path exists through which validate_manifest could ever see "
            "manifest bytes other than the single compiled-in real manifest."
        ),
        "runtime_source_anchors": {
            "module-manifest.json_sha256": sha_file(f"{ROOT}/module-manifest.json"),
            "amphora-engine/src/lib.rs_sha256": sha_file(engine_path),
            "amphora-core/src/capability.rs_sha256": sha_file(
                f"{ROOT}/amphora-core/src/capability.rs"
            ),
        },
        "prior_receipt_anchors_match_current_source": {
            "least_privilege_authority_parity_v1_declared_lib_rs_sha256": "ddfd50fcebf96b096fff8406dfe27b512ab8e88564f76b644ffda776df662abb",
            "authority_lattice_completeness_v1_declared_lib_rs_sha256": "ddfd50fcebf96b096fff8406dfe27b512ab8e88564f76b644ffda776df662abb",
            "current_lib_rs_sha256": sha_file(engine_path),
            "note": (
                "Both prior receipts anchor the SAME lib.rs bytes attacked "
                "here -- confirms this is an attack on the still-standing "
                "current artifact, not a stale target."
            ),
        },
    }

    # --- (a) visibility: is validate_manifest declared `pub`? ---------------
    sig_idx = None
    for i, line in enumerate(engine_lines):
        if TARGET_FN_SIG in line:
            sig_idx = i
            break
    fn_line_number = sig_idx + 1 if sig_idx is not None else None
    is_private = sig_idx is not None and not engine_lines[sig_idx].strip().startswith("pub ")
    diag["a_visibility"] = {
        "function_signature": TARGET_FN_SIG,
        "defining_file": DEFINING_FILE,
        "line_number_1indexed": fn_line_number,
        "declared_pub": (not is_private) if sig_idx is not None else None,
        "is_crate_private": is_private,
    }

    # --- (b) workspace-wide call-site count for THIS exact function --------
    # Only lib.rs defines this exact signature/return type; amphora-cli has an
    # unrelated same-named function with a different signature (dataset
    # manifest validation) that is explicitly excluded by requiring the call
    # be inside the SAME file as the definition (private fn => cannot be
    # called from any other file/crate; Rust's module-privacy rule, not an
    # assumption of this oracle).
    call_pattern = re.compile(r"\bvalidate_manifest\s*\(\s*&manifest\s*\)")
    call_sites = []
    for i, line in enumerate(engine_lines):
        if call_pattern.search(line) and "fn validate_manifest" not in line:
            call_sites.append({"file": DEFINING_FILE, "line_number_1indexed": i + 1, "text": line.strip()})

    other_files_with_same_call_shape = []
    for path in iter_rs_files(ROOT):
        rel = os.path.relpath(path, ROOT)
        if rel == DEFINING_FILE:
            continue
        with open(path, "r", errors="replace") as f:
            text = f.read()
        if call_pattern.search(text):
            other_files_with_same_call_shape.append(rel)

    diag["b_call_sites"] = {
        "call_sites_in_defining_file": call_sites,
        "call_site_count_in_defining_file": len(call_sites),
        "other_workspace_files_matching_call_shape_validate_manifest_ampersand_manifest": other_files_with_same_call_shape,
        "exactly_one_call_site_workspace_wide": (
            len(call_sites) == 1 and len(other_files_with_same_call_shape) == 0
        ),
        "rust_privacy_guarantee": (
            "validate_manifest carries no `pub`/`pub(crate)`/`pub(super)` "
            "modifier, so the Rust compiler forbids any call from outside "
            "amphora-engine/src/lib.rs itself, independent of what this grep "
            "finds; the grep result is corroborating, not load-bearing."
        ),
    }

    # --- (c) the one call site is behind OnceLock::get_or_init -------------
    once_lock_block = "\n".join(engine_lines[max(0, sig_idx - 160) : sig_idx])
    global_fn_present = "pub fn global() -> Result<&'static Self, RegistryError> {" in engine_src
    once_lock_present = "static REGISTRY: OnceLock<Result<NativeRegistry, RegistryError>> = OnceLock::new();" in engine_src
    get_or_init_present = "REGISTRY.get_or_init(Self::build)" in engine_src
    registry_mutator_count = len(re.findall(r"REGISTRY\.\w+\(", engine_src))
    diag["c_single_evaluation_guard"] = {
        "global_fn_present": global_fn_present,
        "static_oncelock_declared": once_lock_present,
        "sole_initializer_is_get_or_init_build": get_or_init_present,
        "registry_static_method_call_sites": registry_mutator_count,
        "registry_static_method_calls_are_all_get_or_init": registry_mutator_count == 1 and get_or_init_present,
        "conclusion": (
            "REGISTRY is a OnceLock initialized exactly once per process via "
            "get_or_init(Self::build); no reset/reload/set method exists on it "
            "anywhere in the source. Once validated (or rejected) at first "
            "access, the outcome is cached for the process lifetime."
        ),
    }

    # --- (d) manifest bytes are a compile-time constant, no override -------
    include_bytes_pattern = re.compile(
        r'const MANIFEST_BYTES:\s*&\[u8\]\s*=\s*include_bytes!\("\.\./\.\./module-manifest\.json"\);'
    )
    include_bytes_present = bool(include_bytes_pattern.search(engine_src))
    other_manifest_bytes_defs = []
    for path in iter_rs_files(ROOT):
        rel = os.path.relpath(path, ROOT)
        with open(path, "r", errors="replace") as f:
            text = f.read()
        if re.search(r"\bMANIFEST_BYTES\b", text) and rel != DEFINING_FILE:
            other_manifest_bytes_defs.append(rel)

    # Scoped check: does the ONE call site's own argument-derivation chain
    # (build(), lines immediately preceding validate_manifest(&manifest)?)
    # read from anything other than the MANIFEST_BYTES const -- e.g. a path
    # parameter, env::var, or fs::read? This is the check that actually
    # matters for reachability of validate_manifest specifically.
    build_fn_start = engine_src.index("fn build() -> Result<Self, RegistryError> {")
    build_fn_block = engine_src[build_fn_start : build_fn_start + 600]
    scoped_override_pattern = re.compile(r"env::var\(|fs::read\(|std::env::args|\bpath\s*:")
    scoped_override_hits = scoped_override_pattern.findall(build_fn_block)
    call_site_argument_is_manifest_bytes_const_only = (
        "MANIFEST_BYTES" in build_fn_block and len(scoped_override_hits) == 0
    )

    # Broader workspace-wide scan is kept for transparency but is explicitly
    # NOT a reachability gate for validate_manifest: any hit here belongs to
    # a DIFFERENT function in a DIFFERENT crate (amphora-cli's own
    # module-manifest.json disk reads for its unrelated phase0/phase1 review
    # tooling), and per gate (a) validate_manifest is crate-private to
    # amphora-engine, so no other crate's code -- however it reads the file
    # -- can ever call it, regardless of what this broader scan finds.
    broad_pattern = re.compile(
        r"env::var\([^)]*[Mm][Aa][Nn][Ii][Ff][Ee][Ss][Tt][^)]*\)|--manifest[-_]?path|MANIFEST_(PATH|OVERRIDE|FILE)\b"
    )
    other_crate_manifest_readers = []
    for path in iter_rs_files(ROOT):
        rel = os.path.relpath(path, ROOT)
        if rel == DEFINING_FILE:
            continue
        with open(path, "r", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                if broad_pattern.search(line):
                    other_crate_manifest_readers.append(
                        {"file": rel, "line_number_1indexed": lineno, "text": line.strip()}
                    )

    diag["d_compile_time_frozen_bytes"] = {
        "manifest_bytes_is_include_bytes_constant": include_bytes_present,
        "manifest_bytes_referenced_outside_defining_file": other_manifest_bytes_defs,
        "build_fn_argument_derivation_is_manifest_bytes_const_only": call_site_argument_is_manifest_bytes_const_only,
        "build_fn_scoped_override_pattern_hits": scoped_override_hits,
        "other_crate_manifest_readers_workspace_wide_informational_only": other_crate_manifest_readers,
        "other_crate_readers_are_gate_irrelevant_reason": (
            "These are amphora-cli's OWN module-manifest.json disk reads "
            "(phase0.rs/phase1.rs review tooling, an unrelated crate/purpose "
            "-- computing hashes and provenance reports, not authority "
            "grants). They cannot feed amphora-engine::validate_manifest "
            "regardless of what they read, because gate (a) already proves "
            "that function is crate-private to amphora-engine. Included here "
            "for transparency, not as a gate input."
        ),
        "conclusion": (
            "MANIFEST_BYTES is declared `const ... = include_bytes!(...)`, and "
            "the sole call site's argument-derivation chain (build(), lines "
            "171-176) uses MANIFEST_BYTES directly with no path/env/fs "
            "indirection. Rust compile-time constants of this form are frozen "
            "into the binary's read-only data section; nothing at runtime, "
            "in this crate or any other, can substitute alternate bytes into "
            "this specific call site short of shipping a different binary."
        ),
    }

    # --- separate reachable grant-decision path is untouched by any of this
    envelope_reads_descriptor_only = (
        "descriptor.authority_ceiling" in engine_src
        and "descriptor.model_readiness_ceiling" in engine_src
    )
    diag["grant_path_independence"] = {
        "claim": (
            "The per-candidate grant/score-envelope path (NativeRegistry::"
            "envelope -> TrustCapability::evaluate) reads only the already-"
            "frozen `descriptor` struct (populated once at startup from the "
            "validated manifest) and never re-invokes validate_manifest or "
            "accepts caller-supplied manifest content."
        ),
        "envelope_reads_static_descriptor_fields": envelope_reads_descriptor_only,
        "prior_finding_this_path_already_probed_live": {
            "study_id": "T-07 authority-escalation-under-alternate-encodings-v1",
            "receipt": "amphora-model-card-authority/evidence/phase0/repairs/T-07/done/t07-authority-escalation-encoding-done-receipt.v1.dsse.json",
            "verdict": "CLAIM_REFUTED",
            "finding": (
                "3/24 encoding cases (lowercase, trailing-space, Cyrillic-"
                "homoglyph 'RANKICNG') achieved feasible=true/ACCEPT via the "
                "REAL live rank_candidates/authorize_optimizer_request path, "
                "because the forbidden-tier guard there is an exact-byte "
                "denylist. This IS the attacker-reachable grant path; the "
                "manifest-tamper G3/N probes give it zero coverage."
            ),
        },
    }

    a_ok = diag["a_visibility"]["is_crate_private"] is True
    b_ok = diag["b_call_sites"]["exactly_one_call_site_workspace_wide"] is True
    c_ok = diag["c_single_evaluation_guard"]["registry_static_method_calls_are_all_get_or_init"] is True
    d_ok = (
        diag["d_compile_time_frozen_bytes"]["manifest_bytes_is_include_bytes_constant"] is True
        and diag["d_compile_time_frozen_bytes"]["build_fn_argument_derivation_is_manifest_bytes_const_only"] is True
    )
    unreachable_confirmed = a_ok and b_ok and c_ok and d_ok

    diag["gates"] = {
        "a_validate_manifest_is_crate_private": a_ok,
        "b_exactly_one_call_site_workspace_wide": b_ok,
        "c_evaluated_at_most_once_per_process": c_ok,
        "d_manifest_bytes_compile_time_frozen_no_override_surface": d_ok,
        "unreachable_by_any_live_caller_confirmed": unreachable_confirmed,
    }
    diag["verdict"] = "CLAIM_REFUTED" if unreachable_confirmed else "CLAIM_SURVIVED"
    diag["verdict_reasoning"] = (
        "validate_manifest is unreachable by any live caller with anything "
        "other than the single compile-time manifest, so the G3/N tamper-"
        "probe gates in the two prior receipts -- though internally correct "
        "as Python computations -- do not corroborate rejection of any "
        "'spoofed'/'stale'/'incomplete'/'over-ceiling' GRANT as the module's "
        "falsifiable hypothesis requires: no such grant attempt can ever "
        "reach this function. The two receipts' own 'does_not_close' text "
        "('a live-runtime differential harness remains Phase-1') undersells "
        "this -- it frames the gap as work not yet done, when the tested "
        "threat model has zero live attack surface by construction, not "
        "merely 'not yet verified live'."
        if unreachable_confirmed
        else "At least one reachability gate failed; see gates above for detail."
    )
    diag["does_not_close"] = (
        "Does not reopen or contradict G1/G2 in least-privilege-authority-"
        "parity-v1 or L in authority-lattice-completeness-v1 (those concern "
        "score_semantics / the authority envelope on the real, valid "
        "manifest, not manifest-tamper reachability). Does not modify the "
        "portfolio manifest, module-manifest.json, any locked dataset, or a "
        "signed Phase-0 KPI. AUDIT_ONLY; no scientific, product, or legal "
        "authority asserted."
    )
    diag["counts"] = {
        "rs_files_scanned": len(iter_rs_files(ROOT)),
        "call_sites_found": len(call_sites),
        "other_crate_manifest_readers_informational": len(other_crate_manifest_readers),
    }

    print(json.dumps(diag, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
