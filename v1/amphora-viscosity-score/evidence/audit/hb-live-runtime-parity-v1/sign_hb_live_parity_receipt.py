#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score HB live-runtime parity audit.
AUDIT_ONLY. Does not modify the master manifest, does not modify any existing signed
receipt or KPI, does not promote any KPI or flip module phase/scientific_readiness."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
EV = MOD / 'evidence/audit/hb-live-runtime-parity-v1'
SEED_DIR = Path.home() / '.local/share/amphora/phase0/keys'
EVAL_SEED = SEED_DIR / 'evaluator.ed25519.seed'
REVIEWER_SEED = SEED_DIR / 'internal-reviewer.ed25519.seed'
TRUST = ROOT / 'config/phase0-trust-store.v1.json'

FIRE_ID = '20260816T070001-3974882-875bdc64dfe1'


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

harness_path = MOD / 'examples/hb_live_runtime_parity_probe.rs'
harness_sha = sha(harness_path.read_bytes())
comparator_path = EV / 'run_hb_live_parity_check.py'
comparator_sha = sha(comparator_path.read_bytes())

live_rust_a = EV / 'hb_live_runA.json'
live_rust_b = EV / 'hb_live_runB.json'
live_rust_a_sha = sha(live_rust_a.read_bytes())
live_rust_b_sha = sha(live_rust_b.read_bytes())
assert live_rust_a_sha == live_rust_b_sha, 'two-replay byte-stability gate FAILED (live cargo run)'

kpi_path = MOD / 'evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json'
kpi_sha = sha(kpi_path.read_bytes())
source_lock_path = MOD / 'evidence/audit/herschel-bulkley-ccby-amorim2021-v1/source_amorim2021_hb_table2.v1.json'
source_lock_sha = sha(source_lock_path.read_bytes())

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
    'schema': 'amphora.viscosity-score.hb-live-runtime-parity-receipt.v1',
    'receipt_id': 'hb-live-runtime-parity-v1',
    'module_id': 'amphora-viscosity-score',
    'authority': 'AUDIT_ONLY',
    'authority_ceiling': 'EVIDENCE_ONLY',
    'phase': 'PRE_PHASE_0',
    'scientific_success_required_for_phase0': False,
    'date': '2026-08-16',
    'fire_id': FIRE_ID,
    'generated_on_host': 'xbabe2 (compute, live cargo run of the compiled crate + CPython comparator); xbabe1 (orchestration)',
    'promotes_authority': False,
    'flips_scientific_readiness': False,
    'human_review_performed': False,
    'organizational_independence_asserted': False,
    'modifies_manifest': False,
    'modifies_locked_dataset': False,
    'modifies_signed_phase0_kpi': False,
    'campaign_item_id': '',
    'claim_under_attack': (
        'evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json (sha256 ' + kpi_sha + '), '
        'promoted 2026-08-04 (V1-KPI-VISC) and re-verified 2026-08-14 (W-VISC2), which asserts '
        '"Herschel-Bulkley yield-flow path (src/lib.rs:1227) evaluated at published fitted '
        'parameters". The underlying scientific receipt\'s own committed source '
        '(evidence/audit/herschel-bulkley-ccby-amorim2021-v1/run_hb_benchmark.py, unchanged since '
        '2026-08-01 across all three prior fires) states in its docstring: "MODULE FORMULA UNDER '
        'TEST (re-derived, not imported, to keep this an independent CPython oracle -- matches '
        'amphora-viscosity-score/src/lib.rs:1227 verbatim)". No prior fire on this claim '
        '(2026-08-01, 2026-08-04, 2026-08-14) ever called the actual compiled Rust primitive -- '
        'all three computed and byte-identically replayed the Python oracle only. The literal '
        '"matches ... verbatim" claim, as written into the promoted KPI\'s own evidentiary chain, '
        'was therefore never actually checked against the compiled code it claims to reproduce.'
    ),
    'attack_description': (
        'Live-runtime (real compiled Rust, not a reimplementation) parity probe. Built a new cargo '
        'example, examples/hb_live_runtime_parity_probe.rs (sha256 ' + harness_sha + '), that calls '
        'the live, unmodified `herschel_bulkley_apparent_viscosity` function (src/lib.rs:1227, '
        'confirmed at that exact line number by direct inspection) at the same 6 formulations x 4 '
        'shear rates as the promoted KPI, using the source fixture\'s own corrected tau0/K/n values '
        '(asserted byte-identical to the committed source-lock JSON, sha256 ' + source_lock_sha + ', '
        'at Rust runtime via assert_source_lock_matches), plus a 10-case guard-rail edge-case '
        'battery (negative/zero/NaN/Infinity yield stress, non-positive consistency/flow-index/'
        'shear-rate). Two independent `cargo run --example` executions produced byte-identical '
        'diagnostics (sha256 ' + live_rust_a_sha + '). A separate CPython comparator '
        '(evidence/audit/hb-live-runtime-parity-v1/run_hb_live_parity_check.py, sha256 ' +
        comparator_sha + ') then diffed the live-Rust output against the SAME "verbatim '
        're-derivation" formula and guard logic used in run_hb_benchmark.py (copied unmodified into '
        'herschel_bulkley_python_oracle), at 1e-9 relative tolerance for the 24 numeric points and '
        'exact Ok/Err agreement for the 10 guard-rail cases. Two independent comparator runs '
        'produced byte-identical diagnostics (sha256 ' + canon_sha + '), satisfying the two-replay '
        'determinism gate.'
    ),
    'method_fidelity_note': (
        'The numeric arithmetic path calls the live compiled `herschel_bulkley_apparent_viscosity` '
        'primitive directly (amphora_viscosity_score::herschel_bulkley_apparent_viscosity) -- the '
        'same public function any downstream caller or the promoted KPI\'s benchmark would use -- '
        'not a Python/CPython re-derivation. The comparator is intentionally a byte-for-byte copy '
        'of the promoted KPI\'s own oracle logic (not an "improved" or "corrected" version), because '
        'the point of this probe is to test whether THAT SPECIFIC, ALREADY-PROMOTED oracle is what '
        'it claims to be, not to write a better one.'
    ),
    'refutation_criterion': (
        'The "matches src/lib.rs:1227 verbatim" claim, as literally written into the promoted '
        'KPI\'s own evidentiary chain (run_hb_benchmark.py docstring), would be REFUTED by observing '
        'EITHER (a) any of the 24 (row, shear_rate) live-Rust values differing from the Python '
        'oracle by more than 1e-9 relative, OR (b) any of the 10 guard-rail edge cases producing a '
        'live-Rust Ok/Err outcome that disagrees with the Python oracle\'s no-raise/raise outcome '
        'for the identical input. It would SURVIVE if all 24 numeric points matched within '
        'tolerance AND all 10 guard-rail cases agreed.'
    ),
    'observed': (
        'All 24 numeric (row, shear_rate) points matched EXACTLY (max_rel_diff = 0.0 -- Rust '
        'f64::powf and CPython\'s ** operator agree bit-for-bit on this platform/libm for every '
        'tested input), confirming the core arithmetic re-derivation IS verbatim. However, 1 of 10 '
        'guard-rail edge cases disagreed: for tau0 = +Infinity (consistency=10, n=0.5, '
        'gamma_dot=1.0), the live compiled Rust primitive correctly returns Err (its guard is '
        '`!yield_stress_pa.is_finite()`, which rejects both NaN and +/-Infinity), but the promoted '
        'KPI\'s own "verbatim" Python oracle returns Ok (its guard is literally '
        '`not (tau0 == tau0) or tau0 < 0.0`, which catches NaN via self-inequality and negative '
        'values, but NOT +Infinity, since Infinity == Infinity is True and Infinity is not < 0.0). '
        'The Python oracle\'s inline comment even mislabels this guard "# is_finite + >=0" -- it is '
        'not actually an is_finite check. This is a real, mechanically demonstrated divergence '
        'between the promoted, signed KPI\'s own claimed-verbatim oracle and the compiled primitive '
        'it claims to reproduce.'
    ),
    'verdict': 'CLAIM_REFUTED',
    'verdict_scope': (
        'REFUTED narrowly and precisely: the literal claim "matches src/lib.rs:1227 verbatim" '
        '(run_hb_benchmark.py docstring, inherited unchanged by the promoted KPI\'s evidentiary '
        'chain across 3 prior fires) is false for the guard-rail/input-validation code path -- the '
        'Python oracle silently ACCEPTS an input (tau0 = +Infinity) that the real compiled Rust '
        'primitive REJECTS. This does NOT refute the promoted KPI\'s actual reported numbers: none '
        'of the 6 published formulations\' tau0/K/n values are non-finite, all 24 tested numeric '
        'points reproduce bit-for-bit, and the physical-plausibility findings (axis-bound '
        'containment, monotonic shear-thinning, ranking reproduction, locale-repair justification) '
        'stand unaffected. The refutation is specifically about the fidelity of the promoted '
        'artifact\'s own "verbatim" characterization of its oracle -- a real integrity gap in what '
        'the signed evidence chain asserts about itself, not a gap in the empirical benchmark '
        'result. If any future benchmark input near +/-Infinity were ever fed through the promoted '
        'oracle (e.g. a malformed upstream unit conversion), it would silently diverge from what '
        'the compiled module actually does.'
    ),
    'positive_control': {
        'planted_defect': 'mutant Python oracle uses gamma_dot**n instead of gamma_dot**(n-1) in the Herschel-Bulkley consistency term -- a wrong-exponent re-derivation bug, the same class of implementation-drift defect this parity check exists to catch',
        'how_planted': 'herschel_bulkley_mutant_oracle() in run_hb_live_parity_check.py: K * (gamma_dot ** n) replaces K * (gamma_dot ** (n - 1.0)); all guard logic and inputs otherwise identical to the real oracle and to the live-Rust call',
        'detected': diag['positive_control']['detected'],
        'evidence': diag['positive_control']['evidence'],
        'note': (
            'Recorded for completeness even though this receipt reports CLAIM_REFUTED (which '
            'carries its own evidence and does not strictly require a positive control): the '
            'mutant exponent bug produces a max relative deviation of ' +
            str(diag['positive_control']['mutant_max_rel_diff']) + ' against the SAME live-Rust '
            'values that matched the real oracle at rel_diff 0.0, proving this comparator '
            'apparatus is genuinely capable of catching a re-derivation/implementation-drift '
            'defect and did not simply pass by construction.'
        ),
    },
    'recommended_repair': (
        'Either (a) fix herschel_bulkley_python_oracle\'s guard in run_hb_benchmark.py from '
        '`not (tau0 == tau0) or tau0 < 0.0` to a real is_finite check (e.g. '
        '`not math.isfinite(tau0) or tau0 < 0.0`) so the docstring\'s "verbatim" claim is true, or '
        '(b) soften the docstring\'s "matches ... verbatim" language to scope it explicitly to the '
        'arithmetic path only, not the guard rails. Not performed in this fire (AUDIT_ONLY, no '
        'src/lib.rs or run_hb_benchmark.py change made or required to land this finding; the '
        'promoted KPI and its underlying receipt are left unmodified per protocol -- superseding, '
        'if desired, is a repair-mode action for a future fire).'
    ),
    'kpi_under_attack_sha256': kpi_sha,
    'source_lock_sha256': source_lock_sha,
    'harness_sha256': {'examples/hb_live_runtime_parity_probe.rs': harness_sha},
    'comparator_sha256': {'run_hb_live_parity_check.py': comparator_sha},
    'reproducibility': {
        'two_replay_byte_identical_live_rust': True,
        'live_rust_diagnostic_sha256': live_rust_a_sha,
        'two_replay_byte_identical_comparator': True,
        'comparator_diagnostic_sha256': canon_sha,
        'command_live_rust': 'cd amphora-viscosity-score && cargo run --quiet --example hb_live_runtime_parity_probe',
        'command_comparator': 'cd amphora-viscosity-score/evidence/audit/hb-live-runtime-parity-v1 && python3 run_hb_live_parity_check.py',
        'determinism': 'pure deterministic floating-point arithmetic on committed constants, no RNG, no network I/O at run time',
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
ptype = 'application/vnd.amphora.viscosity-score-hb-live-runtime-parity+json'
sig = eval_sk.sign(pae(ptype, body))
envelope = {'payload': base64.standard_b64encode(body).decode(), 'payloadType': ptype,
            'signatures': [{'keyid': eval_key_id, 'sig': base64.standard_b64encode(sig).decode()}]}
receipt = {'evaluator_key_id': eval_key_id, 'evaluator_public_key_hex': eval_pub_hex,
           'reviewer_public_key_hex': rev_pub_hex, 'signature': envelope}
out = EV / 'hb-live-runtime-parity-receipt.v1.dsse.json'
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
