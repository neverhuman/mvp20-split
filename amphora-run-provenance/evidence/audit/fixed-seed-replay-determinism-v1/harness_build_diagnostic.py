#!/usr/bin/env python3
"""fixed-seed-replay-determinism-v1 harness.

Tests amphora-run-provenance/docs/mission.md's own stated Phase-0
falsifiable hypothesis verbatim: "fixed-seed replay is byte-identical
outside declared wall-clock telemetry."

No prior fire for this module (hash-chain-oracle-parity-v1,
merkle-rfc6962-baseline-v1, anchor-necessity-reforge-resistance-v1,
live-runtime-archive-parity-v1, real-archive-tamper-scale-v1/T-13,
W-T-PROV) tested cross-run replay determinism directly; all attacked
verify_run's tamper-detection semantics or standards conformance against
a SINGLE archive. This harness instead compares TWO independent, real,
production amphora-cli (binary name amphora-tui) `run` invocations with
IDENTICAL candidate, seed, population, generations, workers, lane, and
objective profile, executed minutes apart on 2026-08-15 (fire
20260815T170001-612230-8379a41d4acd), archives pinned verbatim under
./archives/run-A and ./archives/run-B.

Deterministic and reproducible: reads only the two pinned archive
directories and the pinned amphora-cli/src/main.rs source copy; no
wall-clock, no RNG, no network.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
STUDY = ROOT / "amphora-run-provenance/evidence/audit/fixed-seed-replay-determinism-v1"
RUN_A = STUDY / "archives/run-A"
RUN_B = STUDY / "archives/run-B"
MAIN_RS = ROOT / "amphora-cli/src/main.rs"

RUN_A_ID = "run-1786813446666"
RUN_B_ID = "run-1786813479575"

TIMING_FIELD_NAMES = {"at_ms", "started_at_ms", "average_latency_ms", "duration_ms", "wall_clock_ms"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text())


def load_events(p: Path):
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def flatten(o, prefix=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flatten(v, prefix + "." + k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(flatten(v, prefix + f"[{i}]"))
    else:
        out[prefix] = o
    return out


def diff_flat(a, b):
    fa, fb = flatten(a), flatten(b)
    keys = sorted(set(fa) | set(fb))
    diffs = []
    for k in keys:
        va, vb = fa.get(k, "<MISSING>"), fb.get(k, "<MISSING>")
        if va != vb:
            diffs.append({"path": k, "a": va, "b": vb})
    return diffs


def strip_volatile_event(ev, run_id):
    ev = dict(ev)
    ev.pop("run_id", None)
    ev.pop("event_hash", None)
    ev.pop("previous_event_hash", None)
    payload = ev.get("payload")
    if isinstance(payload, dict):
        payload = dict(payload)
        for k in TIMING_FIELD_NAMES:
            payload.pop(k, None)
        ev["payload"] = payload
    s = json.dumps(ev, sort_keys=True)
    return s.replace(run_id, "<RUN_ID>")


# ---- 1. Pin inputs ----
manifest_a, manifest_b = load_json(RUN_A / "manifest.json"), load_json(RUN_B / "manifest.json")
final_a, final_b = load_json(RUN_A / "final-state.json"), load_json(RUN_B / "final-state.json")
prov_a, prov_b = load_json(RUN_A / "provenance.json"), load_json(RUN_B / "provenance.json")
events_a, events_b = load_events(RUN_A / "events.jsonl"), load_events(RUN_B / "events.jsonl")

archive_file_sha256 = {
    "run-A": {f: sha((RUN_A / f).read_bytes()) for f in sorted(p.name for p in RUN_A.iterdir())},
    "run-B": {f: sha((RUN_B / f).read_bytes()) for f in sorted(p.name for p in RUN_B.iterdir())},
}

# ---- 2. Confirm identical run PARAMETERS (the actual "fixed seed" precondition) ----
cfg_a, cfg_b = manifest_a["configuration"], manifest_b["configuration"]
inputs_equal = {
    "population": cfg_a["population"] == cfg_b["population"],
    "generations": cfg_a["generations"] == cfg_b["generations"],
    "workers": cfg_a["workers"] == cfg_b["workers"],
    "lane": cfg_a["lane"] == cfg_b["lane"],
    "objective_profile_hash": cfg_a["objective_profile_hash"] == cfg_b["objective_profile_hash"],
    "registry_hash": cfg_a["registry_hash"] == cfg_b["registry_hash"],
    "candidate_contract_value_hash": manifest_a["inputs"]["candidate_contract_value_hash"]
    == manifest_b["inputs"]["candidate_contract_value_hash"],
    "amphora_cli_sha256": manifest_a["binaries"]["amphora_cli_sha256"] == manifest_b["binaries"]["amphora_cli_sha256"],
    "cargo_lock_sha256": manifest_a["dependencies"]["cargo_lock_sha256"] == manifest_b["dependencies"]["cargo_lock_sha256"],
}
assert all(inputs_equal.values()), f"precondition violated, inputs not equal: {inputs_equal}"

# NOTE: seed itself is not a manifest field (candidate contract records the
# resulting value hash, not raw args); both invocations were issued with
# the literal CLI flag --seed 20260815, recorded in the fire's shell
# transcript, and the resulting rng block in each event payload is
# identical (see events_content_diff_after_stripping below) which is the
# only artifact-level witness of seed equality available post-hoc.

# ---- 3. Field-level diffs ----
manifest_diffs = diff_flat(manifest_a, manifest_b)
final_state_diffs = diff_flat(final_a, final_b)

events_stripped_a = [strip_volatile_event(e, RUN_A_ID) for e in events_a]
events_stripped_b = [strip_volatile_event(e, RUN_B_ID) for e in events_b]
events_content_diff_after_stripping = [
    {"index": i, "a": sa, "b": sb}
    for i, (sa, sb) in enumerate(zip(events_stripped_a, events_stripped_b))
    if sa != sb
]

provenance_fields = ["run_id", "manifest_sha256", "events_sha256", "event_chain_root", "final_state_hash", "root_hash"]
provenance_compare = {
    f: {"a": prov_a.get(f), "b": prov_b.get(f), "equal": prov_a.get(f) == prov_b.get(f)}
    for f in provenance_fields
}

# ---- 4. Source-level root cause: does `run` (non-demo) use the module's
# OWN deterministic_run_id, or wall-clock now_ms()? ----
main_rs_bytes = MAIN_RS.read_bytes()
main_rs_text = main_rs_bytes.decode()
lines = main_rs_text.splitlines()


def line_containing(needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1, lines[i].strip()
    return None, None


deterministic_fn_line, deterministic_fn_src = line_containing("fn deterministic_run_id(")
scoring_run_id_line, scoring_run_id_src = line_containing("let scoring_run_id = deterministic_run_id(")
run_id_branch_line, run_id_branch_src = line_containing("let run_id = if demo {")
demo_branch_line, demo_branch_src = line_containing("scoring_run_id.clone()")
wallclock_branch_line, wallclock_branch_src = line_containing('format!("run-{}", now_ms())')
archive_path_line, archive_path_src = line_containing('let archive_path = Path::new(".amphora/runs")')

# ---- 5. Search for any DECLARED allowlist of "wall-clock telemetry"
# fields anywhere in the module or its shared runtime, that would let an
# auditor mechanically apply the hypothesis's exemption clause. ----
declared_exemption_hits = []
search_roots = [
    ROOT / "amphora-run-provenance",
    ROOT / "amphora-core",
    ROOT / "amphora-cli",
]
needles = [b"wall_clock", b"wall-clock", b"volatile_field", b"replay_exempt", b"excluded_field",
           b"nondeterministic_field", b"timing_field", b"replay_diff", b"compare_run"]
for root in search_roots:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in (".rs", ".json", ".md") and "evidence/audit/fixed-seed-replay-determinism-v1" not in str(path):
            try:
                content = path.read_bytes()
            except OSError:
                continue
            for n in needles:
                if n in content:
                    declared_exemption_hits.append({"file": str(path.relative_to(ROOT)), "needle": n.decode()})

# ---- 6. Is there any shipped command that cross-compares two runs for
# replay-determinism? `replay --verify` only self-checks ONE archive. ----
replay_fn_line, replay_fn_src = line_containing("fn replay(path: &Path, verify: bool)")

refutation_criterion = (
    "Two independent production `amphora-tui run` invocations "
    "(binary built from amphora-cli, workspace bin name amphora-tui) with "
    "identical --candidate, --seed, --population, --generations, --workers, "
    "--lane, and objective profile produce a DIFFERENT provenance.json "
    "root_hash (the module's sole content-addressable replay-identity "
    "anchor), and the divergent bytes are not confined to any field the "
    "module or its docs DECLARE as exempt wall-clock telemetry."
)
root_hash_differs = provenance_compare["root_hash"]["a"] != provenance_compare["root_hash"]["b"]
uses_wallclock_for_archive_identity = wallclock_branch_line is not None and demo_branch_line is not None
# None of the raw substring hits above is itself a mechanized field-exemption
# list (a schema, an allowlist constant, a set of field names an auditor
# could apply); they are: the hypothesis sentence being tested, an unrelated
# Monte Carlo RNG-source disclaimer, and a single unrelated boolean flag
# ("wall_clock_used") in a different study's diagnostic. Recorded verbatim
# in declared_wall_clock_telemetry_exemption_search.hits for independent
# judgment; none defines which fields of manifest.json/final-state.json/
# provenance.json are permitted to vary under the hypothesis.
mechanized_exemption_list_hits = [
    h for h in declared_exemption_hits
    if h["file"] not in (
        "amphora-run-provenance/docs/mission.md",
        "amphora-run-provenance/reference/mvp20/out/run_manifest.json",
        "amphora-run-provenance/evidence/audit/anchor-necessity-reforge-resistance-v1/diagnostic.canonical.json",
        "amphora-run-provenance/evidence/audit/anchor-necessity-reforge-resistance-v1/diagnostic.runB.json",
    )
]
no_declared_exemption_list = len(mechanized_exemption_list_hits) == 0
refutation_observed = root_hash_differs and uses_wallclock_for_archive_identity and no_declared_exemption_list

diagnostic = {
    "schema": "amphora.run-provenance.fixed-seed-replay-determinism-diagnostic.v1",
    "study_id": "fixed-seed-replay-determinism-v1",
    "module": "amphora-run-provenance",
    "hypothesis_under_test": {
        "source": "amphora-run-provenance/docs/mission.md, section 'Decision and falsifiable hypothesis'",
        "text_verbatim": "This module supports the decision of whether a complete validated run can be replayed from hash-bound inputs. Its falsifiable hypothesis is that fixed-seed replay is byte-identical outside declared wall-clock telemetry.",
    },
    "inputs": {
        "run_a_id": RUN_A_ID,
        "run_b_id": RUN_B_ID,
        "cli_invocation": (
            "./target/release/amphora-tui run "
            "--candidate amphora-candidate-contract/fixtures/molecule_candidate.json "
            "--population 4 --generations 1 --workers 1 --seed 20260815 --headless --jsonl"
        ),
        "invoked_identically_twice": True,
        "inputs_equal_precondition_checks": inputs_equal,
        "archive_file_sha256": archive_file_sha256,
    },
    "results": {
        "manifest_json_flat_diffs": manifest_diffs,
        "manifest_json_diff_count": len(manifest_diffs),
        "final_state_json_flat_diffs": final_state_diffs,
        "final_state_json_diff_count": len(final_state_diffs),
        "events_jsonl_n_events": {"a": len(events_a), "b": len(events_b)},
        "events_jsonl_content_diffs_after_stripping_run_id_and_timing_fields": events_content_diff_after_stripping,
        "events_jsonl_content_diff_count_after_stripping": len(events_content_diff_after_stripping),
        "provenance_json_field_compare": provenance_compare,
        "all_five_hash_anchors_differ": all(
            not provenance_compare[f]["equal"]
            for f in ["manifest_sha256", "events_sha256", "event_chain_root", "final_state_hash", "root_hash"]
        ),
    },
    "root_cause_source_read": {
        "file": "amphora-cli/src/main.rs",
        "deterministic_run_id_fn": {"line": deterministic_fn_line, "src": deterministic_fn_src},
        "scoring_run_id_assignment": {"line": scoring_run_id_line, "src": scoring_run_id_src},
        "archive_run_id_branch_header": {"line": run_id_branch_line, "src": run_id_branch_src},
        "demo_mode_uses_deterministic_id": {"line": demo_branch_line, "src": demo_branch_src},
        "real_run_mode_uses_wallclock_now_ms": {"line": wallclock_branch_line, "src": wallclock_branch_src},
        "archive_path_keyed_by_run_id_not_scoring_run_id": {"line": archive_path_line, "src": archive_path_src},
        "interpretation": (
            "The module already contains a deterministic, seed-derived run "
            "identity function (deterministic_run_id, stable_hash over "
            "candidate+seed+population+generations+workers+lane+profile) "
            "and assigns it to scoring_run_id unconditionally. But the "
            "on-disk archive identity used for .amphora/runs/<run_id> (and "
            "therefore embedded byte-for-byte into manifest.json, into "
            "every event's run_id field in events.jsonl, and transitively "
            "into every provenance.json hash field) is scoring_run_id ONLY "
            "when demo==true. The production `run` subcommand (not `demo`) "
            "takes the else branch and uses format!(\"run-{}\", now_ms()) "
            "instead -- wall-clock milliseconds -- even though nothing "
            "about population/generations/candidate/seed prevented reusing "
            "the deterministic id it already computed one line earlier."
        ),
    },
    "declared_wall_clock_telemetry_exemption_search": {
        "search_roots": [str(r.relative_to(ROOT)) for r in search_roots],
        "needles_searched": [n.decode() for n in needles],
        "hits": declared_exemption_hits,
        "mechanized_exemption_list_hits": mechanized_exemption_list_hits,
        "finding": (
            "4 raw substring hits, none a mechanized field-exemption list: "
            "(1) mission.md's own hypothesis sentence being tested here, "
            "(2) an unrelated Monte Carlo RNG-source disclaimer in "
            "reference/mvp20/out/run_manifest.json ('no wall-clock RNG "
            "source is used'), and (3-4) a single unrelated boolean flag "
            "'wall_clock_used': false inside a DIFFERENT prior study's "
            "diagnostic (anchor-necessity-reforge-resistance-v1), which "
            "records whether THAT harness used wall-clock timing, not a "
            "declaration of which run-provenance archive fields may vary. "
            "Zero hits define an allowlist, schema field, or code constant "
            "naming which manifest.json/final-state.json/provenance.json "
            "fields are permitted to diverge under the hypothesis. There is "
            "no mechanism, shipped or documented, by which an auditor (or "
            "verify_run, or replay --verify) can distinguish 'declared "
            "wall-clock telemetry' from any other diverging byte."
        ),
    },
    "shipped_replay_command_capability": {
        "fn": {"line": replay_fn_line, "src": replay_fn_src},
        "finding": (
            "`amphora-tui replay --run <path> --verify` only re-runs "
            "verify_run against the ONE archive named; the CLI ships no "
            "subcommand that compares two archives, or a fresh run against "
            "a prior one, for replay-determinism. The falsifiable "
            "hypothesis as stated is therefore not testable by any tool "
            "the module ships -- this harness is the first artifact in the "
            "module's history to actually exercise it."
        ),
    },
    "refutation_criterion_verbatim": refutation_criterion,
    "refutation_criterion_observation_occurred": refutation_observed,
    "positive_finding": (
        "The underlying scientific content IS deterministic: after "
        "stripping run_id and the five named timing-telemetry field names "
        "(at_ms, started_at_ms, average_latency_ms, duration_ms, "
        "wall_clock_ms) by hand, all "
        f"{len(events_a)} real events (proposals, mutations, scores, "
        "rankings, result_hash values) are byte-identical between the two "
        "runs -- confirming the sha256-counter-v1 seeded RNG and scoring "
        "path genuinely replay deterministically at the content level. "
        "What is refuted is narrower and more consequential: the module's "
        "own root_hash/verify_run apparatus cannot witness that fact, "
        "because it hashes run_id (wall-clock-derived in production) and "
        "unlabelled real telemetry (average_latency_ms) into the SAME "
        "anchor it holds out as proof of byte-identical replay, with no "
        "declared separation."
    ),
}

canon_bytes = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
(STUDY / "diagnostic.canonical.json").write_bytes(canon_bytes)
print("wrote diagnostic.canonical.json", sha(canon_bytes))
print("root_hash_a", provenance_compare["root_hash"]["a"])
print("root_hash_b", provenance_compare["root_hash"]["b"])
print("refutation_criterion_observation_occurred", refutation_observed)
