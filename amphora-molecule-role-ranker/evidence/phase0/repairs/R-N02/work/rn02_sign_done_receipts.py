#!/usr/bin/env python3
"""R-N02 coordinated C=N fix: sign one done-receipt PER MODULE.

Replicates amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py
(pae / load_seed / payloadType / attestation keys / two-replay gate) and
self-verifies each receipt after writing: reload -> rebuild PAE -> Ed25519
verify against seed-derived pubkey -> assert keyid startswith
phase0-evaluator-3ef6b35.

Signing order is acyclic: rdkit-ffi (A) -> molecule-property (B) ->
molecule-role-ranker (C). Later receipts cite earlier ones by path+sha256;
earlier ones cite later ones by path with sha256 null and an explicit
forward_reference note (a receipt cannot contain the hash of a receipt signed
after it).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FFI = ROOT / "amphora-rdkit-ffi"
MP = ROOT / "amphora-molecule-property"
RR = ROOT / "amphora-molecule-role-ranker"

WORK_MP = MP / "evidence/phase0/repairs/R-N02/work"
WORK_RR = RR / "evidence/phase0/repairs/R-N02/work"

DONE_FFI = FFI / "evidence/phase0/repairs/R-N02/done"
DONE_MP = MP / "evidence/phase0/repairs/R-N02/done"
DONE_RR = RR / "evidence/phase0/repairs/R-N02/done"

REPAIR_ITEM = "R-N02"
REPAIR_MODE = "interactive-2026-08-03"
DATE = "2026-08-03"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fsha(p):
    return sha(Path(p).read_bytes())


def rel(p):
    return str(Path(p).relative_to(ROOT))


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_key_id.startswith("phase0-evaluator-3ef6b35"), eval_key_id

# ---------------------------------------------------------------- inputs
prop_pre = json.loads((WORK_MP / "property_sweep.PRE.runA.json").read_text())
prop_post = json.loads((WORK_MP / "property_sweep.POST.runA.json").read_text())
ffi_pre = json.loads((WORK_RR / "ffi_sweep.PRE.runA.json").read_text())
ffi_post = json.loads((WORK_RR / "ffi_sweep.POST.runA.json").read_text())
reattack_prop = json.loads((WORK_MP / "reattack_guanidine_gap.runA.json").read_text())
reattack_role = json.loads((WORK_RR / "reattack_role_probe.runA.json").read_text())
sibling_probe = json.loads((WORK_RR / "sibling_live_runtime_probe.POST.json").read_text())

# two-replay byte gates
assert (WORK_MP / "property_sweep.PRE.runA.json").read_bytes() == (WORK_MP / "property_sweep.PRE.runB.json").read_bytes()
assert (WORK_MP / "property_sweep.POST.runA.json").read_bytes() == (WORK_MP / "property_sweep.POST.runB.json").read_bytes()
assert (WORK_RR / "ffi_sweep.PRE.runA.json").read_bytes() == (WORK_RR / "ffi_sweep.PRE.runB.json").read_bytes()
assert (WORK_RR / "ffi_sweep.POST.runA.json").read_bytes() == (WORK_RR / "ffi_sweep.POST.runB.json").read_bytes()
assert (WORK_MP / "reattack_guanidine_gap.runA.json").read_bytes() == (WORK_MP / "reattack_guanidine_gap.runB.json").read_bytes()
assert (WORK_RR / "reattack_role_probe.runA.json").read_bytes() == (WORK_RR / "reattack_role_probe.runB.json").read_bytes()

# zero-regression gates
assert prop_pre["regression_records"] == prop_post["regression_records"]
assert ffi_pre["fixture_records"] == ffi_post["fixture_records"]
assert len(prop_post["regression_records"]) == 26
assert len(ffi_post["fixture_records"]) == 39
assert ffi_post["n_fixture_records_matching_fixture_facts"] == 39

REFUTING_A = MP / "evidence/audit/amine-nh-guanidine-conjugation-gap-v1/amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json"
REFUTING_B = RR / "benchmarks/role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json"
BRIDGE = FFI / "src/bridge.cc"
FFI_LIB = FFI / "src/lib.rs"
COMPUTE = MP / "benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py"
MC_LIB = ROOT / "amphora-molecule-capabilities/src/lib.rs"
FIXTURE_V1 = RR / "reference/phase0-role-known-answer.v1.json"
FIXTURE_V2 = RR / "reference/phase0-role-known-answer.v2.json"
KPI_RR = RR / "evidence/phase0/kpis/role-classification-kpi.v1.json"
TARGET_RECEIPT_MP = MP / "benchmarks/amine-class-active-nh-robustness-v1/amine_class_active_nh_robustness_receipt.v1.json"
MANIFEST = MP / "reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
BENCH_MP = MP / "reference/mvp20/data/eew_ahew_benchmark.v1.json"

# pre-repair sha256 of every signed artifact in scope, verified identical after
SUPERSEDED_INTACT = {
    rel(REFUTING_A): "59c447c077a069c18a68fede5308d44c2e52dbc20ba4ba3cc4754f17ac3a4701",
    rel(REFUTING_B): "414a68af76b1db0c658b1d08e757d187122f81874ae2d4612f96808340904099",
    rel(TARGET_RECEIPT_MP): "74e2c759c1f56ba435ad2807be1f2bdc37c479d68fca81934569901072ba6519",
    rel(FIXTURE_V1): "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f",
    rel(KPI_RR): "88689040b9dcce07560c05f1053dd9d0243f1bd084b259e69b5e727cfc528f36",
    rel(RR / "evidence/phase0/benchmark/result.v1.json"): "f2a21f74e03b6b20f53fb10d4cdb6f2b477ce2b9a6e5200947c1ed91ad3a136a",
    rel(RR / "evidence/phase0/benchmark/benchmark-lock.v1.json"): "6960c8cf8f4296aeed47e445148d127f6f5ff51921adb6393780313f84809170",
    rel(MANIFEST): "f5623b3171d65de2dc805b740aef71ad6163554dcf9b5b394d84181b3ad6bf08",
    rel(BENCH_MP): "3de26f203423a80212e6c90aaa511e5112c79bf92ac56b4c63260c3086d4638f",
}
intact_now = {p: fsha(ROOT / p) for p in SUPERSEDED_INTACT}
for p, before in SUPERSEDED_INTACT.items():
    assert intact_now[p] == before, f"SIGNED ARTIFACT MODIFIED: {p}"

SOURCE_SHA_BEFORE = {
    rel(BRIDGE): "62086ec067f0562f75ee9d4eefb2d5246f02ba5e5464fd3d587abd36a0b4696d",
    rel(FFI_LIB): "52cc3a1e57bb82fef46a79b267076d3388765b1d968ee9c1a6843076fa65c045",
    rel(COMPUTE): "ff3649a1dc1001795d06eba7a9cd64f3b933a5abafcfad3893c23cd4a690c53d",
    rel(MC_LIB): "c38e784f57f40f78811a585dfc878f4d76f5e3a9192ec3559dbf63fd88338e35",
}
SOURCE_SHA_AFTER = {p: fsha(ROOT / p) for p in SOURCE_SHA_BEFORE}

THE_RULE = (
    "An N-H nitrogen whose attached carbon bears a C=N double bond to another "
    "nitrogen (amidine/guanidine carbon) is EXCLUDED from active/reactive amine "
    "N-H counts -- exactly symmetric with the pre-existing C=O/C=S "
    "(amide/thioamide) exclusion, and justified by the same physical principle "
    "already stated in the shipped code: delocalization of the nitrogen lone "
    "pair into an adjacent pi-acceptor removes the nucleophilicity required for "
    "1:1 amine+epoxide ring-opening addition."
)

QUANTITATIVE_OPEN = (
    "EXPLICITLY OPEN, NOT CLOSED BY THIS REPAIR: whether guanidine/amidine N-H "
    "is exactly 0 in a QUANTITATIVE (AHEW / equivalent-weight / mix-ratio) "
    "sense. Both refuting receipts scoped themselves the same way "
    "(amine-nh-guanidine-conjugation-gap-v1 ceiling: 'does not assert a single "
    "correct published AHEW number for dicyandiamide'; "
    "role-guanidine-accelerator-domain-probe-v1 does_not_close: 'whether "
    "reactive_amine_hydrogen_count should be exactly 0 for guanidine N-H in a "
    "quantitative AHEW sense (mechanistic nucleophilicity question, out of "
    "scope)'). R-N02 fixes CATEGORICAL CLASSIFICATION ONLY: guanidine-class "
    "molecules no longer present as ordinary stoichiometric amine hardeners. "
    "Any future quantitative latent-hardener AHEW/mix-ratio path must be a "
    "separate, explicitly-flagged code path with its own evidence."
)

CONSUMER_SWEEP = [
    {"path": "amphora-rdkit-ffi/src/bridge.cc",
     "consumes": "defines count_reactive_amine_hydrogens (the fixed function)",
     "inherits_fix_automatically": True,
     "note": "site of the fix: new is_amidine_or_guanidine_carbon() neighbor check added alongside is_carbonyl_carbon/is_sulfonyl_sulfur."},
    {"path": "amphora-rdkit-ffi/src/lib.rs",
     "consumes": "parses the tab-separated facts record field 5 into MoleculeFactsV1.reactive_amine_hydrogen_count and derives reactive_flags",
     "inherits_fix_automatically": True,
     "note": "no logic change needed; R-N02 regression test pinned_native_backend_excludes_guanidine_class_amine_hydrogens added here."},
    {"path": "amphora-molecule-capabilities/src/lib.rs",
     "consumes": "role-ranker inferred_role() + design-gate + property paths read MoleculeFactsV1.reactive_amine_hydrogen_count / reactive_flags",
     "inherits_fix_automatically": True,
     "note": "links amphora-rdkit-ffi (path dependency, feature rdkit -> amphora-rdkit-ffi/rdkit); no logic change needed. R-N02 real-FFI regression test role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi added here."},
    {"path": "amphora-formulation-capabilities/src/lib.rs",
     "consumes": "hardener.reactive_amine_hydrogen_count for AHEW-style mix arithmetic (guards ==0 before dividing)",
     "inherits_fix_automatically": True,
     "note": "links amphora-rdkit-ffi; inherits automatically. Behavior change is fail-closed and desirable: guanidine-class inputs now hit the existing count==0 guard instead of silently yielding a stoichiometric mix ratio -- precisely the latent-hardener hazard flagged by refuting receipt (a)'s third follow-up."},
    {"path": "amphora-cli/src/compound.rs",
     "consumes": "reads reactive_amine_hydrogen_count out of serialized facts JSON for CLI display/report",
     "inherits_fix_automatically": True,
     "note": "links amphora-rdkit-ffi (feature rdkit); presentation only, no own copy of the rule."},
    {"path": "amphora-cli/src/control.rs",
     "consumes": "compares facts.reactive_amine_hydrogen_count against expected values and computes AHEW-style quantities in control flows",
     "inherits_fix_automatically": True,
     "note": "links amphora-rdkit-ffi; inherits automatically. Divides only after an explicit ==0 guard."},
    {"path": "amphora-core/src/molecule_evidence.rs",
     "consumes": "names reactive_amine_hydrogen_count only as a logistic-model feature_order string in a test fixture",
     "inherits_fix_automatically": True,
     "note": "no structural rule of its own; nothing to change."},
    {"path": "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py",
     "consumes": "INDEPENDENT Python re-implementation n_active_amine_nh() (does NOT link the FFI)",
     "inherits_fix_automatically": False,
     "note": "REQUIRED ITS OWN CHANGE and received it: the refuting receipt's own prototyped extension was adopted verbatim (neighbor-carbon double-bond-partner set {O,S} -> {O,S,N}). This is the second half of the coordinated fix."},
    {"path": "amphora-molecule-design-gate/evidence/audit/nitrogen-nucleophilicity-authenticity-v1/design_gate_nucleophilicity_oracle.py",
     "consumes": "AUDIT-ONLY frozen oracle: standalone Python re-derivation of the N-H rule used by an already-signed past audit",
     "inherits_fix_automatically": False,
     "note": "DELIBERATELY NOT MODIFIED. Frozen evidence artifact under evidence/audit/ whose bytes are cited by an already-signed receipt; editing it would rewrite signed evidence (IRON RULE 1). Its verdict is historical and remains attached to the pre-fix bridge.cc it audited. Any future re-audit must be a NEW v2 artifact alongside."},
    {"path": "amphora-molecule-design-gate/evidence/audit/rdkit-structural-facts-parity-v1/design_gate_oracle.py",
     "consumes": "AUDIT-ONLY frozen parity oracle re-deriving structural facts incl. reactive amine H",
     "inherits_fix_automatically": False,
     "note": "DELIBERATELY NOT MODIFIED, same reason. A future parity re-run against post-fix bridge.cc must be a NEW audit artifact; this receipt records the divergence explicitly rather than silently editing signed evidence."},
    {"path": "amphora-molecule-design-gate/evidence/audit/smiles-representation-invariance-v1/design_gate_repr_invariance_oracle.py",
     "consumes": "AUDIT-ONLY frozen representation-invariance oracle",
     "inherits_fix_automatically": False,
     "note": "DELIBERATELY NOT MODIFIED, same reason. Its invariance conclusion is representation-level and unaffected in kind by the categorical rule change."},
    {"path": "amphora-molecule-design-gate/evidence/audit/fact-snapshot-authority-v1/{analyze.py,make_probes.py,live_harness/src/main.rs}",
     "consumes": "AUDIT-ONLY frozen fact-snapshot authority probes; the live_harness links the FFI",
     "inherits_fix_automatically": True,
     "note": "The live_harness links amphora-rdkit-ffi so a re-run would pick the fix up automatically; the frozen .py analysis artifacts are NOT modified (signed evidence). Not re-run under R-N02: its claim is about snapshot authority, not N-H chemotype."},
    {"path": "amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1/harness/src/main.rs",
     "consumes": "the ORIGINAL refuting attack harness (b); links the real FFI",
     "inherits_fix_automatically": True,
     "note": "UNMODIFIED and re-run verbatim as the R-N02 re-attack: same probes, same hardcoded SMILES, same scoring. Verdict flipped HYPOTHESIS_REFUTED -> HYPOTHESIS_CORROBORATED."},
    {"path": "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/harness/src/main.rs",
     "consumes": "prior hostile-null domain probe (BDMA/EMI-24/DICY/...); links the real FFI",
     "inherits_fix_automatically": True,
     "note": "UNMODIFIED and re-run as an extra regression check: 9/9 scored probes still pass post-fix. Its DICY probe was deliberately UNSCORED (expected_role None, 'OPEN CHEMISTRY QUESTION'); post-fix DICY reads reactive_amine_hydrogen_count=0 / out_of_domain, consistent with the categorical rule and with that probe's own open-question framing."},
    {"path": "amphora-molecule-role-ranker/benchmarks/{role-fact-provenance-invariance-v1,role-flory-gelation-v1,role-macosko-miller-sol-latitude-v1,role-parsimony-conformal-v1,role-reactivity-ratio-substitution-effect-v1}/*.py",
     "consumes": "read reactive_amine_hydrogen_count from the 39-record fixture / model features; no structural N-H rule of their own",
     "inherits_fix_automatically": True,
     "note": "They consume fixture-recorded counts, not the rule. Fixture v1's 39 records are byte-unchanged under the fix (verified 39/39 via the real FFI), so these are unaffected."},
    {"path": "amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1/compute_guanidine_gap.py",
     "consumes": "the ORIGINAL refuting attack (a); extracts n_active_amine_nh() VERBATIM from compute_amine_class.py at runtime",
     "inherits_fix_automatically": True,
     "note": "UNMODIFIED and re-run verbatim as the R-N02 re-attack. Because it extracts the shipped function by source marker at runtime, it now extracts the FIXED function: verdict flipped REFUTED -> SURVIVED."},
]


def envelope_and_write(body_obj, ptype, out_path):
    body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
    sig = eval_sk.sign(pae(ptype, body))
    env = {"payload": base64.standard_b64encode(body).decode(),
           "payloadType": ptype,
           "signatures": [{"keyid": eval_key_id,
                           "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id,
               "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex,
               "signature": env}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    # ---- SELF-VERIFY: reload from disk, rebuild PAE, verify, check keyid
    reloaded = json.loads(out_path.read_text())
    renv = reloaded["signature"]
    rbody = base64.standard_b64decode(renv["payload"])
    rsig = base64.standard_b64decode(renv["signatures"][0]["sig"])
    Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(reloaded["evaluator_public_key_hex"])).verify(
            rsig, pae(renv["payloadType"], rbody))
    assert bytes.fromhex(reloaded["evaluator_public_key_hex"]) == eval_pub
    assert renv["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), \
        renv["signatures"][0]["keyid"]
    assert json.loads(rbody) == body_obj
    print("SELF-VERIFIED", rel(out_path))
    print("  payload_canonical_sha256", sha(body))
    print("  receipt_sha256", fsha(out_path))
    return {"path": rel(out_path), "receipt_sha256": fsha(out_path),
            "payload_canonical_sha256": sha(body)}


def common_block(module):
    return {
        "repair_item": REPAIR_ITEM,
        "repair_mode": REPAIR_MODE,
        "module": module,
        "date": DATE,
        "generated_on_host": "xbabe2",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_benchmark_lock": False,
        "modifies_no_live_config": True,
        "the_rule": THE_RULE,
        "quantitative_question_status": QUANTITATIVE_OPEN,
        "coordinated_repair": (
            "One categorical rule, applied consistently across two independent "
            "implementations refuted the same day (2026-08-03): the C++ production "
            "FFI amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens "
            "(18:08 ledger / receipt (b)) and the Python AHEW rule "
            "amphora-molecule-property .../compute_amine_class.py::n_active_amine_nh "
            "(19:09 ledger / receipt (a)). Three done-receipts, one per module, "
            "cross-referenced."
        ),
        "refuting_receipts": [
            {"role": "refuting receipt (a) -- molecule-property n_active_amine_nh",
             "path": rel(REFUTING_A), "sha256": fsha(REFUTING_A),
             "verdict": "REFUTED", "ledger_fire": "20260803T180001-2431769-2ec3a78bbee1",
             "deleted_or_modified": False},
            {"role": "refuting receipt (b) -- bridge.cc count_reactive_amine_hydrogens via real FFI",
             "path": rel(REFUTING_B), "sha256": fsha(REFUTING_B),
             "verdict": "CLAIM_REFUTED", "ledger_fire": "20260803T190001-3122084-a08778b76bbe",
             "deleted_or_modified": False},
        ],
        "signed_artifacts_verified_intact": [
            {"path": p, "sha256_before": SUPERSEDED_INTACT[p],
             "sha256_after": intact_now[p],
             "identical": SUPERSEDED_INTACT[p] == intact_now[p],
             "deleted_or_modified": False}
            for p in sorted(SUPERSEDED_INTACT)
        ],
        "source_code_edits": [
            {"path": p, "sha256_before": SOURCE_SHA_BEFORE[p],
             "sha256_after": SOURCE_SHA_AFTER[p],
             "changed": SOURCE_SHA_BEFORE[p] != SOURCE_SHA_AFTER[p]}
            for p in sorted(SOURCE_SHA_BEFORE)
        ],
        "consumer_sweep": CONSUMER_SWEEP,
        "cargo_test_results": {
            "amphora-rdkit-ffi --features rdkit": "ok. 7 passed; 0 failed; 0 ignored (incl. new pinned_native_backend_excludes_guanidine_class_amine_hydrogens)",
            "amphora-molecule-capabilities --features rdkit": "lib ok. 45 passed; 0 failed (incl. new role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi); role_ranker_phase0_kpi ok 1 passed; property_phase0_kpi ok 1 passed; design_gate_phase0_kpi ok 1 passed; molecule_novelty_phase0_kpi ok 1 passed; molecule_generator_phase0_kpi ok 1 passed",
            "cargo check --workspace": "Finished dev profile; 0 errors",
            "toolkit": "RDKit C++ 2026.03.2 pinned, exact_version_match=true",
        },
        "reattack": {
            "method": "Both ORIGINAL refuting attacks re-run UNMODIFIED (same harness bytes, same hardcoded probe SMILES, same scoring, no reseeding: neither attack uses an RNG or wall clock).",
            "attack_a_property": {
                "harness": rel(MP / "evidence/audit/amine-nh-guanidine-conjugation-gap-v1/compute_guanidine_gap.py"),
                "harness_unmodified": True,
                "verdict_before": "REFUTED", "verdict_after": reattack_prop["verdict"],
                "attack_fires_on_all_probes_after": reattack_prop["gates"]["attack_fires_on_all_probes"],
                "n_probes_shipped_rule_counts_as_active_amine_after": reattack_prop["gates"]["n_probes_shipped_rule_counts_as_active_amine"],
                "regression_all_match_after": reattack_prop["gates"]["regression_all_match_shipped_vs_extended"],
                "n_regression_records_checked": reattack_prop["gates"]["n_regression_records_checked"],
                "observed_probes": [
                    {"id": p["id"],
                     "n_active_nh_SHIPPED_RULE_before": {"guanidine": 4, "dicyandiamide": 4, "biguanide": 5}[p["id"]],
                     "n_active_nh_SHIPPED_RULE_after": p["n_active_nh_SHIPPED_RULE"],
                     "theoretical_ahew_after": p["theoretical_ahew_SHIPPED_RULE"]}
                    for p in reattack_prop["probe_molecules"]],
                "interpretation": "The attack extracts n_active_amine_nh() verbatim from the shipped file at runtime, so post-fix it extracts the FIXED function; shipped and extended rule now agree everywhere and the pre-registered refute criterion no longer fires.",
                "two_replay_sha256": sha((WORK_MP / 'reattack_guanidine_gap.runA.json').read_bytes()),
            },
            "attack_b_role_ranker": {
                "harness": rel(RR / "benchmarks/role-guanidine-accelerator-domain-probe-v1/harness/src/main.rs"),
                "harness_unmodified": True,
                "verdict_before": "HYPOTHESIS_REFUTED", "verdict_after": reattack_role["verdict"],
                "summary_after": reattack_role["summary"],
                "observed_probes": [
                    {"id": r["id"],
                     "observed_reactive_amine_hydrogen_count_before": 3,
                     "observed_reactive_amine_hydrogen_count_after": r["observed_reactive_amine_hydrogen_count"],
                     "observed_role_before": "hardener",
                     "observed_role_after": r["observed_role"],
                     "expected_role": r["expected_role"], "pass_after": r["pass"]}
                    for r in reattack_role["results"]],
                "toolkit_provenance": reattack_role["toolkit_provenance"],
                "two_replay_sha256": sha((WORK_RR / 'reattack_role_probe.runA.json').read_bytes()),
            },
            "five_of_five_probes_now_correct": True,
            "five_probe_summary": [
                {"id": p["id"], "reactive_amine_hydrogen_count": p["reactive_amine_hydrogen_count"],
                 "inferred_role": p["inferred_role"], "via": "real production RDKit FFI"}
                for p in ffi_post["probe_records"]],
            "sibling_prior_probe_regression": {
                "harness": rel(RR / "benchmarks/role-live-runtime-domain-probe-v1/harness/src/main.rs"),
                "verdict_after": sibling_probe.get("verdict"),
                "summary_after": sibling_probe.get("summary"),
                "note": "Prior SURVIVED hostile-null probe re-run unmodified post-fix: all 9 scored probes still pass. Its DICY probe is deliberately unscored (declared OPEN CHEMISTRY QUESTION) and now reads count=0/out_of_domain, consistent with the categorical rule and with the quantitative question staying open.",
            },
        },
        "zero_regression_evidence": {
            "molecule_property_26_records": {
                "n_records": len(prop_post["regression_records"]),
                "byte_identical_pre_vs_post_fix": prop_pre["regression_records"] == prop_post["regression_records"],
                "records": prop_post["regression_records"],
                "pre_sweep_sha256": sha((WORK_MP / "property_sweep.PRE.runA.json").read_bytes()),
                "post_sweep_sha256": sha((WORK_MP / "property_sweep.POST.runA.json").read_bytes()),
                "composition": "3 exact anchors + 6 monodisperse + 13 amine-class grid + 7 nonamine controls + 1 hydroxyl probe (enumerated exactly as the refuting receipt enumerated them)",
            },
            "role_ranker_39_record_fixture": {
                "fixture_path": rel(FIXTURE_V1),
                "fixture_sha256": ffi_post["fixture_sha256"],
                "fixture_modified": False,
                "n_records": ffi_post["n_fixture_records"],
                "n_matching_fixture_recorded_facts": ffi_post["n_fixture_records_matching_fixture_facts"],
                "byte_identical_pre_vs_post_fix": ffi_pre["fixture_records"] == ffi_post["fixture_records"],
                "pre_sweep_sha256": sha((WORK_RR / "ffi_sweep.PRE.runA.json").read_bytes()),
                "post_sweep_sha256": sha((WORK_RR / "ffi_sweep.POST.runA.json").read_bytes()),
                "method": "every fixture record re-derived through the REAL production FFI pre- and post-fix; both runs agree with each other and with the fixture's own recorded facts (39/39).",
            },
        },
        "reproducibility": {
            "two_replay_sha256_gate": "PASS",
            "replays": 2,
            "independent_runs": True,
            "determinism_basis": "no RNG, no wall clock, fixed hardcoded probe lists, sorted-key canonical JSON; every artifact below produced byte-identical output on two independent process invocations.",
            "artifacts_sha256": {
                "property_sweep.PRE": sha((WORK_MP / "property_sweep.PRE.runA.json").read_bytes()),
                "property_sweep.POST": sha((WORK_MP / "property_sweep.POST.runA.json").read_bytes()),
                "ffi_sweep.PRE": sha((WORK_RR / "ffi_sweep.PRE.runA.json").read_bytes()),
                "ffi_sweep.POST": sha((WORK_RR / "ffi_sweep.POST.runA.json").read_bytes()),
                "reattack_guanidine_gap": sha((WORK_MP / "reattack_guanidine_gap.runA.json").read_bytes()),
                "reattack_role_probe": sha((WORK_RR / "reattack_role_probe.runA.json").read_bytes()),
            },
        },
        "rights_check": "No new external data source opened or acquired. All probe molecules are CAS-identified public-domain chemical identities evaluated purely structurally via the already-licensed pinned RDKit backend; all regression records are already-in-tree, already-hash-pinned artifacts.",
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
            "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY repair done-receipt under evidence/phase0/repairs/R-N02/done/",
            "signs_phase0_evaluation_or_review": False,
            "derives_pinned_trust_store_key_id": bool(eval_pin)},
        "reviewer_reference": {
            "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
            "public_key_hex": rev_pub_hex,
            "derives_pinned_trust_store_key_id": bool(rev_pin),
            "reviewer_signature_present": False,
            "note": "Reviewer key referenced for provenance only; no independent human review performed."},
    }


FWD = {"sha256": None,
       "forward_reference": "signed after this receipt in the coordinated R-N02 batch; content-addressing is acyclic, so this receipt's own sha256 is embedded there instead"}

# ================================================================ A: rdkit-ffi
a = common_block("amphora-rdkit-ffi")
a.update({
    "schema": "amphora.rdkit-ffi.rn02-coordinated-cn-fix-repair-receipt.v1",
    "receipt_id": "rn02-rdkit-ffi-coordinated-cn-fix",
    "objective": (
        "Repair the categorical classification defect refuted on 2026-08-03 in "
        "amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens: the "
        "function excluded only carbonyl/thiocarbonyl (C=O/C=S) and sulfonyl "
        "neighbors, never an amidine/guanidine carbon (C=N), so real guanidine-"
        "class cure ACCELERATORS (DPG CAS 102-06-7, DOTG CAS 97-39-2) were "
        "misclassified as stoichiometric hardeners through the real production FFI."
    ),
    "supersedes": {
        "superseded_path": rel(REFUTING_B),
        "superseded_sha256": fsha(REFUTING_B),
        "superseded_deleted_or_modified": False,
        "reason": (
            "Supersedes the DEFECT STATE that refuting receipt (b) documented, not "
            "the receipt itself: (b) is byte-intact and its CLAIM_REFUTED verdict "
            "against the pre-fix bridge.cc stands as a correct historical finding. "
            "What is superseded is the shipped behavior it refuted. Corrected value: "
            "count_reactive_amine_hydrogens now returns 0 (was 3) for DPG and DOTG, "
            "so inferred_role becomes out_of_domain (was hardener), matching (b)'s "
            "expected_role on 2/2 scored probes."
        ),
        "repair_item": REPAIR_ITEM, "repair_mode": REPAIR_MODE,
    },
    "corrected_values_with_derivation": {
        "function": "amphora-rdkit-ffi/src/bridge.cc::count_reactive_amine_hydrogens",
        "derivation": (
            "New file-local helper is_amidine_or_guanidine_carbon(atom): true iff atom "
            "is carbon (atomicNum 6) and bears a DOUBLE bond whose other atom is "
            "nitrogen (atomicNum 7) -- structurally identical in form to the existing "
            "is_carbonyl_carbon (which tests for a DOUBLE bond to O or S). It is added "
            "to the same neighbor-exclusion disjunction already applied per candidate "
            "N-H nitrogen: excluded if any neighbor is_carbonyl_carbon OR "
            "is_sulfonyl_sulfur OR is_amidine_or_guanidine_carbon. All other predicates "
            "(aromatic-N exclusion, formal-charge exclusion, zero-H skip) are untouched."
        ),
        "before_after_probes": [
            {"id": p["id"], "smiles": p["smiles"],
             "reactive_amine_hydrogen_count_before": {r["id"]: r["reactive_amine_hydrogen_count"] for r in ffi_pre["probe_records"]}[p["id"]],
             "reactive_amine_hydrogen_count_after": p["reactive_amine_hydrogen_count"],
             "inferred_role_before": {r["id"]: r["inferred_role"] for r in ffi_pre["probe_records"]}[p["id"]],
             "inferred_role_after": p["inferred_role"],
             "formula": p["formula"], "mw": p["average_molecular_weight_g_mol"]}
            for p in ffi_post["probe_records"]],
    },
    "tests_added": [
        {"crate": "amphora-rdkit-ffi", "file": "src/lib.rs",
         "test": "pinned_native_backend_excludes_guanidine_class_amine_hydrogens",
         "gated": "#[cfg(feature = \"rdkit\")] -- runs through the REAL production FFI",
         "asserts": "DPG, DOTG, guanidine, DICY, biguanide -> reactive_amine_hydrogen_count==0, has_reactive_amine_hydrogen==false, dual_role==false, oxirane_ring_count==0; plus unchanged controls DETA=5, acetamide=0, N-acetylethylenediamine=2."}],
    "cross_references": [
        {"module": "amphora-molecule-property", "path": rel(DONE_MP / "rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json"), **FWD},
        {"module": "amphora-molecule-role-ranker", "path": rel(DONE_RR / "rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json"), **FWD},
    ],
    "retraction_index_entries": [
        {"module": "amphora-molecule-property", "path": "amphora-molecule-property/evidence/phase0/kpis/RETRACTION-INDEX.md", "appended": True},
        {"module": "amphora-molecule-role-ranker", "path": "amphora-molecule-role-ranker/evidence/phase0/kpis/RETRACTION-INDEX.md", "appended": True},
        {"module": "amphora-rdkit-ffi", "appended": False, "reason": "amphora-rdkit-ffi has no evidence/phase0/kpis surface and holds no KPI claims; per the R-N02 spec the index entries belong to molecule-property and molecule-role-ranker."},
    ],
    "why": (
        "The refuting receipt (b) was correct and its fix is now shipped. bridge.cc "
        "applied its own stated exclusion principle to one pi-acceptor chemotype "
        "(C=O/C=S) but not to the mechanistically identical C=N (amidine/guanidine) "
        "chemotype. The minimal symmetric extension makes the predicate consistent: "
        "5/5 coordinated probes (DPG, DOTG, guanidine, DICY, biguanide) now derive "
        "reactive_amine_hydrogen_count=0 and fail closed to out_of_domain through the "
        "real FFI, while all 39 role-ranker fixture records and all 26 molecule-"
        "property regression records are byte-identical pre- and post-fix. Both "
        "original attacks, re-run unmodified, now corroborate."
    ),
})
res_a = envelope_and_write(
    a, "application/vnd.amphora.rdkit-ffi-rn02-coordinated-cn-fix-repair+json",
    DONE_FFI / "rn02-rdkit-ffi-coordinated-cn-fix-repair-receipt.v1.dsse.json")

# ================================================================ B: property
b = common_block("amphora-molecule-property")
b.update({
    "schema": "amphora.molecule-property.rn02-coordinated-cn-fix-repair-receipt.v1",
    "receipt_id": "rn02-molecule-property-coordinated-cn-fix",
    "objective": (
        "Repair the categorical classification defect refuted on 2026-08-03 in "
        "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/"
        "compute_amine_class.py::n_active_amine_nh(): it excluded amide N-H "
        "(C=O/C=S neighbor) but not amidine/guanidine N-H (C=N neighbor), silently "
        "counting dicyandiamide (DICY -- the dominant commercial latent DGEBA "
        "hardener), guanidine and biguanide as fully-active amines and emitting a "
        "confident finite theoretical AHEW for them."
    ),
    "supersedes": {
        "superseded_path": rel(REFUTING_A),
        "superseded_sha256": fsha(REFUTING_A),
        "superseded_deleted_or_modified": False,
        "reason": (
            "Supersedes the DEFECT STATE that refuting receipt (a) documented, not "
            "the receipt itself: (a) is byte-intact and its REFUTED verdict against "
            "the pre-fix n_active_amine_nh() stands as a correct historical finding. "
            "Corrected values, adopting (a)'s own prototyped minimal symmetric "
            "extension verbatim: guanidine n_active_nh 4 -> 0 (theoretical AHEW "
            "14.768 -> undefined/not-applicable), dicyandiamide 4 -> 0 (AHEW 21.0205 "
            "-> undefined), biguanide 5 -> 0 (AHEW 20.2226 -> undefined). 'Undefined' "
            "here means the M/n stoichiometric AHEW rule does not apply to this "
            "class, NOT that a quantitative equivalent weight has been determined "
            "to be infinite."
        ),
        "repair_item": REPAIR_ITEM, "repair_mode": REPAIR_MODE,
    },
    "corrected_values_with_derivation": {
        "function": "amphora-molecule-property/benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py::n_active_amine_nh",
        "derivation": (
            "Adopted verbatim from refuting receipt (a)'s own prototyped extension "
            "(n_active_amine_nh_EXTENDED in compute_guanidine_gap.py): the existing "
            "neighbor-carbon double-bond-partner membership test is widened from "
            "('O','S') to ('O','S','N'). One symbol added to one existing set; no "
            "other predicate touched (aromatic-N exclusion, formal-charge exclusion, "
            "and the multiple-bond-ON-the-N exclusion for imine/nitrile/azo/N=O all "
            "unchanged). Receipt (a) pre-registered and demonstrated that this is a "
            "STRICT generalization: it changes nothing on any of the 26 already-"
            "validated records, which R-N02 re-verified independently."
        ),
        "before_after_probes": [
            {"id": p["id"], "smiles": p["smiles"], "formula": p["formula"], "mw": p["mw"],
             "n_active_nh_before": {r["id"]: r["n_active_nh"] for r in prop_pre["probe_molecules"]}[p["id"]],
             "n_active_nh_after": p["n_active_nh"],
             "theoretical_ahew_before": {r["id"]: r["theoretical_ahew"] for r in prop_pre["probe_molecules"]}[p["id"]],
             "theoretical_ahew_after": p["theoretical_ahew"]}
            for p in prop_post["probe_molecules"]],
        "note_on_dpg_dotg": (
            "DPG and DOTG were probes of the SIBLING module's refutation, but are "
            "swept here too for cross-module rule consistency: pre-fix the Python "
            "rule counted 2 active N-H for each (the FFI counted 3 -- the difference "
            "is the guanidine =N-H, which the Python rule already excluded via its "
            "multiple-bond-on-the-N test while the C++ rule did not); post-fix both "
            "implementations agree at 0 for both molecules."
        ),
    },
    "tests_added": [
        {"crate": "n/a (Python benchmark script)",
         "coverage": "The R-N02 sweep harness evidence/phase0/repairs/R-N02/work/rn02_property_sweep.py runs the shipped n_active_amine_nh() (extracted verbatim by source marker, same technique as the refuting attack) over all 26 previously-validated records plus the 5 coordinated probes, pre- and post-fix, twice each.",
         "result": "26/26 records byte-identical pre vs post; 5/5 probes flip to n_active_nh=0."},
        {"crate": "amphora-rdkit-ffi", "file": "src/lib.rs",
         "test": "pinned_native_backend_excludes_guanidine_class_amine_hydrogens",
         "note": "the C++ half of the coordinated rule is regression-tested in the FFI crate through the real backend."},
        {"crate": "amphora-molecule-capabilities", "file": "src/lib.rs",
         "test": "role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi",
         "note": "end-to-end real-FFI guard covering the same 5 molecules."},
    ],
    "scope_note": (
        "This repair does NOT reopen or contradict any of the 13 tested amine "
        "structures, the 3 exact anchors, the 6 monodisperse records, the 7 nonamine "
        "controls or the hydroxyl probe -- all 26 are re-verified byte-identical "
        "pre- and post-fix. The AHEW=M/n rule and the amine-class robustness "
        "receipt's arithmetic on those records stand unchanged; what is repaired is "
        "the rule's applicability boundary, which now fails closed on the "
        "amidine/guanidine chemotype instead of silently emitting a stoichiometric "
        "AHEW for latent hardeners."
    ),
    "cross_references": [
        {"module": "amphora-rdkit-ffi", "path": res_a["path"],
         "sha256": res_a["receipt_sha256"],
         "payload_canonical_sha256": res_a["payload_canonical_sha256"]},
        {"module": "amphora-molecule-role-ranker", "path": rel(DONE_RR / "rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json"), **FWD},
    ],
    "retraction_index_entry": {
        "path": "amphora-molecule-property/evidence/phase0/kpis/RETRACTION-INDEX.md",
        "appended": True,
        "retracted_claim": (
            "amine_class_active_nh_robustness_receipt.v1.json's generalization claim "
            "that the module's active-N-H structure rule classifies active amine N-H "
            "correctly for the amine-hardener structure class as a whole "
            "(amine_grid_classification_accuracy=1.0, nonamine_fail_closed_rate=1.0 "
            "generalizing beyond the 13 tested structures)."
        ),
        "what_stands": (
            "The receipt's arithmetic on its own 26 records stands (re-verified "
            "byte-identical). Only the generalization to the guanidine/amidine "
            "subclass was refuted, and R-N02 repairs it."
        ),
    },
    "why": (
        "Refuting receipt (a) showed the shipped rule applied its own stated "
        "physical principle (lone-pair delocalization into an adjacent pi-acceptor "
        "removes epoxide-addition nucleophilicity) to amide N but not to "
        "mechanistically identical amidine/guanidine N, producing a confident finite "
        "AHEW (e.g. DICY 84.082/4 = 21.02 g/eq) for the dominant commercial latent "
        "DGEBA hardener class. R-N02 adopts (a)'s own prototyped extension: all 3 of "
        "its probes plus the sibling module's DPG/DOTG now count 0 active N-H, all "
        "26 previously-validated records are unchanged, and (a) re-run unmodified "
        "now returns SURVIVED."
    ),
})
res_b = envelope_and_write(
    b, "application/vnd.amphora.molecule-property-rn02-coordinated-cn-fix-repair+json",
    DONE_MP / "rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json")

# ================================================================ C: role-ranker
c = common_block("amphora-molecule-role-ranker")
c.update({
    "schema": "amphora.molecule-role-ranker.rn02-coordinated-cn-fix-repair-receipt.v1",
    "receipt_id": "rn02-molecule-role-ranker-coordinated-cn-fix",
    "objective": (
        "Record, for the role-ranker module, the coordinated C=N categorical fix "
        "that repairs the domain-generalization defect refuted on 2026-08-03 by "
        "role-guanidine-accelerator-domain-probe-v1: guanidine-class cure "
        "accelerators (DPG, DOTG) were promoted to stoichiometric 'hardener' by the "
        "deterministic role rule because the FFI counted their guanidine N-H as "
        "reactive."
    ),
    "supersedes": {
        "superseded_path": rel(REFUTING_B),
        "superseded_sha256": fsha(REFUTING_B),
        "superseded_deleted_or_modified": False,
        "reason": (
            "Supersedes the DEFECT STATE documented by receipt (b), not the receipt: "
            "(b) is byte-intact and its CLAIM_REFUTED verdict stands historically. "
            "Corrected values via the real production FFI: DPG "
            "reactive_amine_hydrogen_count 3 -> 0 and role hardener -> out_of_domain; "
            "DOTG 3 -> 0 and hardener -> out_of_domain; both now match (b)'s own "
            "expected_role on 2/2 scored probes."
        ),
        "repair_item": REPAIR_ITEM, "repair_mode": REPAIR_MODE,
    },
    "kpi_status": {
        "kpi_path": rel(KPI_RR),
        "kpi_sha256": fsha(KPI_RR),
        "kpi_modified": False,
        "arithmetic_stands": True,
        "statement": (
            "The KPI's structural_inference_agreement_rate=1.0 ARITHMETIC STANDS. The "
            "sha-locked 39-record fixture contains no amidine/guanidine record, so no "
            "fixture record was ever mis-scored by this bug -- independently verified "
            "under R-N02 by re-deriving all 39 records through the real FFI both "
            "pre- and post-fix and obtaining byte-identical results that also match "
            "the fixture's own recorded facts (39/39). What refuting receipt (b) "
            "refuted, and what R-N02 repairs, is the GENERALIZATION INFERENCE drawn "
            "from that 1.0: that the deterministic role rule fails closed on real "
            "out-of-domain accelerator chemotypes generally. The guanidine chemotype "
            "is now handled, and is regression-guarded by the new tests cited below "
            "and by fixture v2."
        ),
    },
    "fixture_v2": {
        "new_path": rel(FIXTURE_V2), "new_sha256": fsha(FIXTURE_V2),
        "n_records": 44,
        "supersedes": {
            "superseded_path": rel(FIXTURE_V1),
            "superseded_sha256": fsha(FIXTURE_V1),
            "superseded_deleted_or_modified": False,
            "reason": (
                "The sha-locked v1 fixture is cited by sha in signed receipts and is "
                "IMMUTABLE; it was not touched (before/after sha256 identical, recorded "
                "above). Per both refuting receipts' follow-up ('Add DPG- and DOTG-class "
                "guanidine accelerators to the module's own 39-record known-answer "
                "fixture'), v2 is created ALONGSIDE: v1's 39 records carried over "
                "byte-identical plus 5 appended guanidine-class out_of_domain records "
                "(DPG, DOTG, guanidine, DICY, biguanide) whose facts derive from the "
                "post-fix production FFI."
            ),
        },
        "v1_records_embedded_byte_identically": True,
        "not_yet_wired_into_kpi": (
            "v2 is published as evidence only. The Phase-0 KPI harness "
            "amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs still reads "
            "v1, and the signed KPI/result/benchmark-lock remain bound to v1's sha -- "
            "deliberately, so this repair does not silently re-baseline a signed KPI. "
            "Promoting v2 into the KPI is a separate, explicitly-evidenced step."
        ),
    },
    "tests_added": [
        {"crate": "amphora-molecule-capabilities", "file": "src/lib.rs",
         "test": "role_ranker_fails_closed_on_guanidine_class_accelerators_via_real_ffi",
         "gated": "#[cfg(feature = \"rdkit\")] -- THROUGH THE REAL FFI, not synthesized facts",
         "asserts": "For DPG, DOTG, guanidine, DICY and biguanide: molecule_facts() gives oxirane_ring_count==0 and reactive_amine_hydrogen_count==0; inferred_role==out_of_domain; and the full role-ranker capability returns status INSUFFICIENT_INPUT, role_fit_status ABSTAINED_AMBIGUOUS_OR_OUT_OF_DOMAIN, empty objective_values and role_ranking_authorized==false."},
        {"crate": "amphora-rdkit-ffi", "file": "src/lib.rs",
         "test": "pinned_native_backend_excludes_guanidine_class_amine_hydrogens",
         "note": "backend-level guard for the same 5 molecules."},
    ],
    "cross_references": [
        {"module": "amphora-rdkit-ffi", "path": res_a["path"],
         "sha256": res_a["receipt_sha256"],
         "payload_canonical_sha256": res_a["payload_canonical_sha256"]},
        {"module": "amphora-molecule-property", "path": res_b["path"],
         "sha256": res_b["receipt_sha256"],
         "payload_canonical_sha256": res_b["payload_canonical_sha256"]},
    ],
    "retraction_index_entry": {
        "path": "amphora-molecule-role-ranker/evidence/phase0/kpis/RETRACTION-INDEX.md",
        "appended": True,
        "retracted_claim": (
            "The generalization inference from role-classification-kpi.v1.json's "
            "structural_inference_agreement_rate=1.0 (plus the prior "
            "role-live-runtime-domain-probe-v1 SURVIVED verdict) that the "
            "deterministic role rule fails closed on real out-of-domain "
            "accelerator/catalyst chemotypes generally."
        ),
        "what_stands": (
            "The KPI arithmetic itself (1.0 on the 39-record fixture) stands; the "
            "fixture contains no guanidine record and was untouched by the bug, "
            "re-verified 39/39 through the real FFI pre- and post-fix."
        ),
    },
    "why": (
        "Both real, CAS-verified guanidine-class accelerators DPG and DOTG were "
        "classified 'hardener' by the live production runtime because bridge.cc's "
        "exclusion predicate never checked for a C=N neighbor. With the coordinated "
        "categorical rule shipped, both fail closed to out_of_domain exactly as the "
        "module's earlier BDMA/EMI-24 hostile nulls do, the original attack re-run "
        "unmodified now returns HYPOTHESIS_CORROBORATED (2/2 probes pass, 0 "
        "disagreements), the earlier live-runtime probe still passes 9/9, and the "
        "39-record fixture is bit-for-bit unaffected."
    ),
})
res_c = envelope_and_write(
    c, "application/vnd.amphora.molecule-role-ranker-rn02-coordinated-cn-fix-repair+json",
    DONE_RR / "rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json")

index = {"repair_item": REPAIR_ITEM, "repair_mode": REPAIR_MODE,
         "receipts": [res_a, res_b, res_c],
         "evaluator_key_id": eval_key_id,
         "eval_derives_pinned_trust_store_key_id": bool(eval_pin)}
(WORK_RR / "rn02_receipt_index.json").write_text(
    json.dumps(index, indent=2, sort_keys=True))
print(json.dumps(index, indent=2, sort_keys=True))
