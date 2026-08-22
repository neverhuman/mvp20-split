#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Grunberg-Nissan live-runtime interaction-wiring
audit. AUDIT_ONLY. Does not modify the master manifest, does not modify any existing signed
receipt or KPI, does not promote any KPI or flip module phase/scientific_readiness, does not
change src/lib.rs."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
EV = MOD / 'evidence/audit/gn-degenerate-ideal-mixing-v1'
SEED_DIR = Path.home() / '.local/share/amphora/phase0/keys'
EVAL_SEED = SEED_DIR / 'evaluator.ed25519.seed'
REVIEWER_SEED = SEED_DIR / 'internal-reviewer.ed25519.seed'
TRUST = ROOT / 'config/phase0-trust-store.v1.json'

FIRE_ID = '20260819T190001-3204491-90761336a8e3'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b'DSSEv1 ' + str(len(t)).encode() + b' ' + t.encode() + b' ' +
            str(len(body)).encode() + b' ' + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (EV / 'diagnostic.canonical.json').read_bytes()
runB = (EV / 'diagnostic.runB.json').read_bytes()
canon_sha = sha(canon)
assert canon_sha == sha(runB), 'two-replay byte-stability gate FAILED (python comparator)'
diag = json.loads(canon)

harness_path = MOD / 'examples/gn_live_runtime_interaction_wiring_probe.rs'
harness_sha = sha(harness_path.read_bytes())
comparator_path = EV / 'run_gn_wiring_check.py'
comparator_sha = sha(comparator_path.read_bytes())

live_rust_a = EV / 'gn_live_runA.json'
live_rust_b = EV / 'gn_live_runB.json'
live_rust_a_sha = sha(live_rust_a.read_bytes())
live_rust_b_sha = sha(live_rust_b.read_bytes())
assert live_rust_a_sha == live_rust_b_sha, 'two-replay byte-stability gate FAILED (live cargo run)'

lib_rs_path = MOD / 'src/lib.rs'
lib_rs_sha = sha(lib_rs_path.read_bytes())
assert lib_rs_sha == diag['lib_rs_sha256'], 'src/lib.rs mutated between live run and sign'

assert diag['call_site_scan']['production_call_site_count'] == 1
assert diag['call_site_scan']['every_call_site_supplies_hardcoded_zero_matrix'] is True
assert diag['interaction_field_scan']['no_schema_field_carries_interaction_data'] is True
assert all(c['within_1e_9'] for c in diag['numeric_checks'].values())
assert diag['zero_vs_nonzero_interaction_rel_diff'] > 0.2

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f'phase0-evaluator-{sha(eval_pub)}'
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f'phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}'
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {'keys': []}
tbr = {k.get('role'): k for k in trust.get('keys', [])}
eval_pin = (eval_key_id == tbr.get('PHASE0_EVALUATOR', {}).get('key_id'))
rev_pin = (rev_key_id == tbr.get('PHASE0_INTERNAL_REVIEWER', {}).get('key_id'))

body_obj = {
    'schema': 'amphora.viscosity-score.gn-degenerate-ideal-mixing-receipt.v1',
    'receipt_id': 'gn-degenerate-ideal-mixing-v1',
    'module_id': 'amphora-viscosity-score',
    'authority': 'AUDIT_ONLY',
    'authority_ceiling': 'EVIDENCE_ONLY',
    'phase': 'PRE_PHASE_0',
    'scientific_success_required_for_phase0': False,
    'date': '2026-08-19',
    'fire_id': FIRE_ID,
    'generated_on_host': 'xbabe2 (compute, live cargo run of the compiled crate + CPython comparator + static source scan); xbabe1 (orchestration)',
    'promotes_authority': False,
    'flips_scientific_readiness': False,
    'human_review_performed': False,
    'organizational_independence_asserted': False,
    'modifies_manifest': False,
    'modifies_locked_dataset': False,
    'modifies_signed_phase0_kpi': False,
    'modifies_src_lib_rs': False,
    'campaign_item_id': '',
    'claim_under_attack': (
        'The standing claim in docs/mission.md ("...the module\'s built-in Grunberg-Nissan blend '
        'mixing, Krieger-Dougherty pigment crowding, and Herschel-Bulkley yield flow paths remain '
        'scientifically UNVALIDATED and require wet-lab formulation rheology for Phase-1"), which '
        'frames Grunberg-Nissan blend mixing (grunberg_nissan_mix, src/lib.rs:1171-1206, cited to '
        'Grunberg, L.; Nissan, A.H. "Mixture Law for Viscosity", Nature 164:799-800 (1949), '
        'doi:10.1038/164799b0, per reference/rheology/source-landscape.v1.json source_id '
        '"grunberg-nissan-1949") as structurally on par with Krieger-Dougherty and Herschel-Bulkley: '
        'a real, implemented physical model merely awaiting wet-lab data before Phase-1, i.e. a '
        'DATA gap rather than an ARCHITECTURE gap.'
    ),
    'attack_description': (
        'Live-runtime (real compiled Rust, not a reimplementation) wiring audit of '
        'grunberg_nissan_mix and its sole call site inside theory_apparent_viscosity. Built a new '
        'cargo example, examples/gn_live_runtime_interaction_wiring_probe.rs (sha256 ' + harness_sha +
        '), that calls the live, unmodified grunberg_nissan_mix and theory_apparent_viscosity '
        'functions three ways: (a) exactly as the production call site invokes it (all-zero '
        'interaction matrix), (b) the same fractions/viscosities with a non-zero, order-unity '
        'interaction term -- the term that is the Grunberg-Nissan equation\'s defining feature over '
        'plain ideal mixing -- and (c) an independent closed-form ideal-mixing computation that '
        'never calls grunberg_nissan_mix at all. It also drives theory_apparent_viscosity end-to-end '
        'on a live two-liquid RheologyObservationV1 (the same function called by both fit_model and '
        'predict, i.e. every training row and every scored candidate). Two independent `cargo run '
        '--example` executions produced byte-identical diagnostics (sha256 ' + live_rust_a_sha + '). '
        'A separate CPython comparator (evidence/audit/gn-degenerate-ideal-mixing-v1/'
        'run_gn_wiring_check.py, sha256 ' + comparator_sha + ') independently re-derived all three '
        'numeric results from scratch (never reusing the Rust arithmetic), cross-checked them against '
        'the live-Rust output at 1e-9 relative tolerance, and performed a static, brace-depth-aware '
        'structural scan of src/lib.rs enumerating every call site of grunberg_nissan_mix in the '
        'entire crate and every line matching "interaction" (case-insensitive) anywhere in the module, '
        'to establish whether ANY code path -- production or test -- ever supplies a non-zero '
        'interaction term, and whether any schema field exists that could carry one. Two independent '
        'comparator runs produced byte-identical diagnostics (sha256 ' + canon_sha + '), satisfying '
        'the two-replay determinism gate.'
    ),
    'refutation_criterion': (
        'The claim that Grunberg-Nissan blend mixing is a real, implemented-but-data-starved '
        'physical model (structurally on par with Krieger-Dougherty/Herschel-Bulkley) would SURVIVE '
        'if grunberg_nissan_mix were invoked anywhere in the live production path (theory_'
        'apparent_viscosity, reached from fit_model and predict) with a non-degenerate (non-zero) '
        'interaction matrix, OR if any schema field existed capable of carrying real Grunberg-Nissan '
        'd_ij interaction data into that call. It would be REFUTED by observing (a) the sole '
        'production call site hardcodes an all-zero interaction matrix with no code path to '
        'override it, AND (b) no field in RheologyObservationV1, LiquidComponentV1, '
        'PigmentComponentV1, or RheologyAdditiveV1 (the complete set of structs reachable from the '
        'observation used to fit/predict) carries interaction-parameter data, AND (c) the omitted '
        'term is numerically material -- i.e. supplying real interaction data to the underlying '
        'function (which is not itself broken) changes its output by more than a token amount.'
    ),
    'observed': (
        'production_call_site_count = ' + str(diag['call_site_scan']['production_call_site_count']) +
        ' (src/lib.rs:1285, inside theory_apparent_viscosity, reached by fit_model at line ' +
        str(diag['theory_apparent_viscosity_callers'][0]) + ' and predict at line ' +
        str(diag['theory_apparent_viscosity_callers'][1]) + '). every_call_site_supplies_hardcoded_'
        'zero_matrix = True across ALL THREE call sites in the crate (the 1 production site AND '
        'both of the function\'s own unit tests at lines 2034/2049 -- there is no unit test anywhere '
        'exercising a non-zero interaction term either). no_schema_field_carries_interaction_data = '
        'True: exhaustive scan of every line matching "interaction" (case-insensitive) in src/lib.rs '
        'found none outside grunberg_nissan_mix\'s own definition and its three call sites. The '
        'independent pure-Python re-derivation confirms the live-Rust zero-interaction result '
        '(' + str(diag['numeric_checks']['gn_zero_interaction_py_vs_rust']['rust']) + ' Pa.s) is '
        'bit-equivalent (rel_diff 0.0) to plain ideal log-linear mixing computed with no reference '
        'to grunberg_nissan_mix at all, and that a non-zero, order-unity interaction term changes '
        'the result by ' + f"{diag['zero_vs_nonzero_interaction_rel_diff']:.1%}" + ' -- large and '
        'squarely in the regime where real Grunberg-Nissan d_ij values fall for non-ideal binary '
        'liquid systems, so the omitted term is not a rounding-level nicety. The end-to-end probe on '
        'a live two-liquid RheologyObservationV1 through the actual theory_apparent_viscosity '
        'function returns ' + str(diag['end_to_end_theory_apparent_viscosity_two_liquid_observation_pa_s']) +
        ' Pa.s, matching (to the small additive Krieger-Dougherty/Herschel-Bulkley terms with '
        'pigment_volume_fraction=0 and negligible yield-flow contribution) the same ideal-mixing '
        'value, confirming the production call chain reaches the identical degenerate branch, not '
        'just the isolated function.'
    ),
    'verdict': 'CLAIM_REFUTED',
    'verdict_scope': (
        'REFUTED precisely: the mission.md framing of Grunberg-Nissan blend mixing as a real '
        'implemented-but-unvalidated physical model, awaiting only wet-lab data like Krieger-'
        'Dougherty and Herschel-Bulkley, is false. As actually wired, the live runtime is '
        'architecturally incapable of ever computing anything other than ideal (zero-interaction) '
        'mixing for ANY candidate, regardless of what data becomes available in the future -- '
        'because (1) the sole production call site hardcodes the interaction matrix to all zeros '
        'with no override path, and (2) no schema field exists anywhere in the observation record '
        'to carry real interaction-parameter data even if a wet-lab source supplied it. This is a '
        'stricter defect than a data gap: sourcing a rights-clean binary-interaction-parameter '
        'dataset (as C9/W-VISC1/W-VISC2 did for Krieger-Dougherty) would NOT be sufficient to '
        'validate Grunberg-Nissan mixing here without a code change to plumb the interaction term '
        'through the schema and the call site first. This does not change the module\'s '
        'scientific_readiness (still UNVALIDATED) or operational_readiness (still SHADOW) -- it '
        'sharpens WHY the Grunberg-Nissan path is unvalidated, from "no data yet" to "no code path '
        'for the data to enter through yet."'
    ),
    'recommended_repair': (
        'Add a schema field (e.g. `binary_interaction_parameters: BTreeMap<(String, String), f64>` '
        'or an equivalent keyed structure) to RheologyObservationV1 (or a sibling reference table) '
        'to carry real Grunberg-Nissan d_ij values, and change the theory_apparent_viscosity call '
        'site (src/lib.rs:1284-1285) to build the interactions matrix from that data instead of '
        'hardcoding zeros. Not performed in this fire (AUDIT_ONLY; no src/lib.rs change made or '
        'required to land this finding). A future repair item should also update docs/mission.md to '
        'disclose this finding and distinguish the Grunberg-Nissan architecture gap from the '
        'Krieger-Dougherty/Herschel-Bulkley data gaps it is currently lumped together with.'
    ),
    'harness_sha256': {'examples/gn_live_runtime_interaction_wiring_probe.rs': harness_sha},
    'comparator_sha256': {'run_gn_wiring_check.py': comparator_sha},
    'lib_rs_sha256_at_audit_time': lib_rs_sha,
    'reproducibility': {
        'two_replay_byte_identical_live_rust': True,
        'live_rust_diagnostic_sha256': live_rust_a_sha,
        'two_replay_byte_identical_comparator': True,
        'comparator_diagnostic_sha256': canon_sha,
        'command_live_rust': 'cd amphora-viscosity-score && cargo run --quiet --example gn_live_runtime_interaction_wiring_probe',
        'command_comparator': 'cd amphora-viscosity-score/evidence/audit/gn-degenerate-ideal-mixing-v1 && python3 run_gn_wiring_check.py',
        'determinism': 'pure deterministic floating-point arithmetic and static regex/brace-depth source scan on committed source, no RNG, no network I/O at run time',
    },
    'full_diagnostic': diag,
    'signing_key': {
        'role': 'PHASE0_EVALUATOR', 'key_id': eval_key_id, 'public_key_hex': eval_pub_hex,
        'used_for': 'AUDIT_ONLY falsification-attack receipt under evidence/audit/',
        'signs_phase0_evaluation_or_review': False,
        'derives_pinned_trust_store_key_id': bool(eval_pin)},
    'reviewer_reference': {
        'role': 'PHASE0_INTERNAL_REVIEWER', 'key_id': rev_key_id, 'public_key_hex': rev_pub_hex,
        'derives_pinned_trust_store_key_id': bool(rev_pin), 'reviewer_signature_present': False,
        'note': 'Reviewer key referenced for provenance only; no independent human review performed.'},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = 'application/vnd.amphora.viscosity-score-gn-degenerate-ideal-mixing+json'
sig = eval_sk.sign(pae(ptype, body))
envelope = {'payload': base64.standard_b64encode(body).decode(), 'payloadType': ptype,
            'signatures': [{'keyid': eval_key_id, 'sig': base64.standard_b64encode(sig).decode()}]}
receipt = {'evaluator_key_id': eval_key_id, 'evaluator_public_key_hex': eval_pub_hex,
           'reviewer_public_key_hex': rev_pub_hex, 'signature': envelope}
out = EV / 'gn-degenerate-ideal-mixing-receipt.v1.dsse.json'
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope['signatures'][0]['sig']),
    pae(ptype, base64.standard_b64decode(envelope['payload'])))
print('WROTE', out)
print('evaluator_key_id', eval_key_id)
print('eval_derives_pinned_trust_key', eval_pin)
print('reviewer_derives_pinned_trust_key', rev_pin)
print('receipt_sha256', sha(out.read_bytes()))
print('signature_verified', True)
