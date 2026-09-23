#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score KD live-runtime parity audit.
AUDIT_ONLY. Does not modify the master manifest, does not modify any existing signed
receipt or KPI, does not promote any KPI or flip module phase/scientific_readiness."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
EV = MOD / 'evidence/audit/kd-live-runtime-parity-v1'
SEED_DIR = Path.home() / '.local/share/amphora/phase0/keys'
EVAL_SEED = SEED_DIR / 'evaluator.ed25519.seed'
REVIEWER_SEED = SEED_DIR / 'internal-reviewer.ed25519.seed'
TRUST = ROOT / 'config/phase0-trust-store.v1.json'

FIRE_ID = '20260818T010001-1464625-87b500ba0d0f'


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

harness_path = MOD / 'examples/kd_live_runtime_parity_probe.rs'
harness_sha = sha(harness_path.read_bytes())
comparator_path = EV / 'run_kd_live_parity_check.py'
comparator_sha = sha(comparator_path.read_bytes())

live_rust_a = EV / 'kd_live_runA.json'
live_rust_b = EV / 'kd_live_runB.json'
live_rust_a_sha = sha(live_rust_a.read_bytes())
live_rust_b_sha = sha(live_rust_b.read_bytes())
assert live_rust_a_sha == live_rust_b_sha, 'two-replay byte-stability gate FAILED (live cargo run)'

wvisc2_path = MOD / 'evidence/phase0/repairs/W-VISC2/done/krieger-dougherty-benchmark-landed-v1/krieger-dougherty-benchmark-landed-receipt.v1.dsse.json'
wvisc2_sha = sha(wvisc2_path.read_bytes())
wvisc1_path = MOD / 'evidence/phase0/repairs/W-VISC1/attempts/krieger-dougherty-ccby-reachability-probe-v1/krieger-dougherty-ccby-reachability-probe-receipt.v1.dsse.json'
wvisc1_sha = sha(wvisc1_path.read_bytes())

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
    'schema': 'amphora.viscosity-score.kd-live-runtime-parity-receipt.v1',
    'receipt_id': 'kd-live-runtime-parity-v1',
    'module_id': 'amphora-viscosity-score',
    'authority': 'AUDIT_ONLY',
    'authority_ceiling': 'EVIDENCE_ONLY',
    'phase': 'PRE_PHASE_0',
    'scientific_success_required_for_phase0': False,
    'date': '2026-08-18',
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
        'The claim, inherited unchanged across every prior Krieger-Dougherty fire (C9 fire1 '
        '2026-08-01, C9 fire2 2026-08-01, W-VISC1 2026-08-05 sha256 ' + wvisc1_sha + ', W-VISC2 '
        '2026-08-14 sha256 ' + wvisc2_sha + '), that the Python `kd_vec` re-derivation used in '
        'every promoted KD benchmark is "replicated verbatim from src/lib.rs:1208-1224" (verbatim '
        'docstring language in run_kd_positive_control.py, itself citing run_kd_ccby_'
        'reachability_probe.py). That cited line range (src/lib.rs:1208-1224) spans the FULL '
        'krieger_dougherty function, including its four input-validity guard clauses '
        '(src/lib.rs:1211-1218: liquid_viscosity finite-positive, pigment_volume_fraction in '
        '[0,1], maximum_packing_fraction in [0,1], pigment_volume_fraction < maximum_packing_'
        'fraction, intrinsic_viscosity finite-positive) -- not just the closed-form output line. '
        'No prior KD fire ever called the actual compiled Rust primitive; all four computed '
        'against a hand-written Python kd_vec re-derivation that implements ONLY the arithmetic '
        'output line and contains NO guard logic at all.'
    ),
    'attack_description': (
        'Live-runtime (real compiled Rust, not a reimplementation) parity probe, escalating the '
        'method that found hb-live-runtime-parity-v1 CLAIM_REFUTED (fire_id 20260816T070001-'
        '3974882-875bdc64dfe1) for HERSCHEL_BULKLEY, applied here to KRIEGER_DOUGHERTY for the '
        'first time. Built a new cargo example, examples/kd_live_runtime_parity_probe.rs (sha256 '
        + harness_sha + '), that calls the live, unmodified `krieger_dougherty` function '
        '(src/lib.rs:1208, confirmed at that exact line number by direct inspection) at (a) the '
        '2x5=10 (fit, phi) points from the promoted W-VISC2 fitted curves (fixed-Einstein and '
        'free-intrinsic-viscosity fits, verbatim parameters from '
        'evidence/phase0/repairs/W-VISC2/done/krieger-dougherty-benchmark-landed-v1/'
        'diagnostic.canonical.json), and (b) a 10-case guard-rail battery covering all four '
        'validity clauses plus a valid-baseline sanity case. Two independent `cargo run '
        '--example` executions produced byte-identical diagnostics (sha256 ' + live_rust_a_sha +
        '). A separate CPython comparator (evidence/audit/kd-live-runtime-parity-v1/'
        'run_kd_live_parity_check.py, sha256 ' + comparator_sha + ') then diffed the live-Rust '
        'output against the SAME "verbatim" kd_vec formula (copied unmodified from the promoted '
        'benchmark scripts, no guard added) at 1e-9 relative tolerance for the 10 numeric points, '
        'and classified each guard-rail case by whether the unguarded Python oracle raises, or '
        'silently returns a finite-real / nan / inf / complex value, versus the live-Rust Ok/Err '
        'outcome. Two independent comparator runs produced byte-identical diagnostics (sha256 ' +
        canon_sha + '), satisfying the two-replay determinism gate.'
    ),
    'method_fidelity_note': (
        'The numeric arithmetic path calls the live compiled `krieger_dougherty` primitive '
        'directly (amphora_viscosity_score::krieger_dougherty) -- the same public function any '
        'downstream caller or the promoted benchmark would use -- not a Python/CPython '
        're-derivation. The comparator\'s oracle is intentionally a byte-for-byte copy of the '
        'promoted benchmarks\' own kd_vec logic (not an "improved" or "corrected" version), '
        'because the point of this probe is to test whether THAT SPECIFIC, ALREADY-PROMOTED '
        'oracle is what its own docstring claims it is, not to write a better one.'
    ),
    'refutation_criterion': (
        'The "replicated verbatim from src/lib.rs:1208-1224" claim (covering both the closed-form '
        'arithmetic AND the four guard/validity clauses at lines 1211-1218) would be REFUTED by '
        'observing EITHER (a) any of the 10 (fit, phi) live-Rust numeric points differing from '
        'the Python kd_vec oracle by more than 1e-9 relative, OR (b) any of the 10 guard-rail '
        'edge cases where the live-Rust Ok/Err outcome disagrees with whether the unguarded '
        'Python oracle produces a finite real (sane) value vs. raises or produces nan/inf/complex. '
        'It would SURVIVE only if all numeric points matched within tolerance AND all guard-rail '
        'cases agreed.'
    ),
    'observed': (
        'All 10 (fit, phi) numeric points matched EXACTLY (max_rel_diff = ' +
        str(diag['numeric_max_rel_diff']) + ' -- Rust f64::powf and CPython\'s ** operator agree '
        'bit-for-bit on this platform/libm for every tested in-domain input), confirming the '
        'core arithmetic re-derivation IS verbatim. But only ' +
        str(diag['guard_rail_agree_count']) + '/' + str(diag['guard_rail_total_count']) +
        ' guard-rail edge cases agreed. 5 of 10 disagreed: for negative_liquid_viscosity, '
        'zero_liquid_viscosity, negative_pigment_fraction, max_packing_fraction_over_one, and '
        'negative_intrinsic_viscosity, the live compiled Rust primitive correctly returns Err '
        '(its four guard clauses at src/lib.rs:1211-1218 reject each of these), but the promoted '
        'benchmarks\' "verbatim" Python kd_vec oracle -- which has NO guard logic at all -- '
        'silently computes and returns a plausible-looking finite real number for every one of '
        'them (e.g. eta_liquid=-1.0 silently produces eta=-2.828 Pa.s; a negative intrinsic '
        'viscosity of -1.0 silently produces eta=0.660 Pa.s). This is a starker gap than the '
        'analogous HB finding (hb-live-runtime-parity-v1, which found 1/10 guard divergences on '
        'an oracle that at least attempted to replicate guard logic): here, the "verbatim '
        'replication" claim explicitly names the full line range including the guard clauses, '
        'yet the guard clauses were never implemented at all. (The other 5 guard-rail cases -- '
        'pigment_fraction_over_one, max_packing_equals boundary, the non-integer-exponent '
        'negative-base case, NaN propagation, and the valid-baseline sanity check -- happen to '
        'agree, but only because CPython\'s ** silently produces a complex number, raises '
        'ZeroDivisionError, or propagates NaN for those specific inputs -- not because the '
        'oracle validates anything.)'
    ),
    'verdict': 'CLAIM_REFUTED',
    'verdict_scope': (
        'REFUTED narrowly and precisely: the literal claim "replicated verbatim from '
        'src/lib.rs:1208-1224" is false for the guard-rail/input-validation code path (lines '
        '1211-1218 of that cited range) -- the Python oracle silently ACCEPTS and numerically '
        'evaluates 5 of 10 tested invalid inputs (negative/zero liquid viscosity, negative '
        'pigment fraction, out-of-range packing fraction, negative intrinsic viscosity) that the '
        'real compiled Rust primitive REJECTS by design. This does NOT refute the promoted W-'
        'VISC1/W-VISC2 findings\' actual reported numbers: the 10 tested in-domain fitted-curve '
        'points reproduce bit-for-bit, and the underpowered-near-phi_max limitation those '
        'receipts already disclose stands unaffected. The refutation is specifically about the '
        'fidelity of the promoted artifacts\' own "verbatim" self-description -- a real integrity '
        'gap in what the signed evidence chain asserts about itself, in the same family as (but '
        'more severe than) the hb-live-runtime-parity-v1 finding. If any future KD benchmark '
        'input strayed outside the physically valid domain (e.g. a bad density-assumption unit '
        'conversion producing a negative or out-of-range phi), the promoted oracle would silently '
        'report a numeric answer where the compiled module would fail closed.'
    ),
    'positive_control': {
        'planted_defect': 'mutant Python oracle uses -eta_intr * phi instead of -eta_intr * phi_max in the Krieger-Dougherty exponent -- a wrong-exponent re-derivation bug, the same class of implementation-drift defect this parity check exists to catch',
        'how_planted': 'kd_vec_mutant_wrong_exponent() in run_kd_live_parity_check.py: (1 - phi/phi_max) ** (-eta_intr * phi) replaces (1 - phi/phi_max) ** (-eta_intr * phi_max); all other logic identical to the real oracle and to the live-Rust call',
        'detected': diag['positive_control']['detected'],
        'evidence': diag['positive_control']['evidence'],
        'note': (
            'Recorded for completeness even though this receipt reports CLAIM_REFUTED (which '
            'carries its own evidence and does not strictly require a positive control): the '
            'mutant exponent bug produces a max relative deviation of ' +
            str(diag['positive_control']['mutant_max_rel_diff']) + ' against the SAME live-Rust '
            'values that matched the real oracle at rel_diff 0.0, proving this comparator '
            'apparatus is genuinely capable of catching a re-derivation/implementation-drift '
            'defect on the arithmetic path and did not simply pass by construction.'
        ),
    },
    'recommended_repair': (
        'Either (a) add real guard logic to kd_vec (or a wrapper) in run_kd_ccby_reachability_'
        'probe.py / run_kd_positive_control.py reproducing src/lib.rs:1211-1218 exactly, so the '
        '"verbatim" claim is true across the cited line range, or (b) narrow the docstring\'s '
        '"replicated verbatim from src/lib.rs:1208-1224" language to explicitly scope it to the '
        'arithmetic output line only (e.g. "src/lib.rs:1222-1223"), not the guard rails. Not '
        'performed in this fire (AUDIT_ONLY, no src/lib.rs or benchmark-script change made or '
        'required to land this finding; the promoted W-VISC1/W-VISC2 receipts are left unmodified '
        'per protocol -- superseding, if desired, is a repair-mode action for a future fire).'
    ),
    'kd_wvisc1_attempt_receipt_sha256': wvisc1_sha,
    'kd_wvisc2_done_receipt_sha256': wvisc2_sha,
    'harness_sha256': {'examples/kd_live_runtime_parity_probe.rs': harness_sha},
    'comparator_sha256': {'run_kd_live_parity_check.py': comparator_sha},
    'reproducibility': {
        'two_replay_byte_identical_live_rust': True,
        'live_rust_diagnostic_sha256': live_rust_a_sha,
        'two_replay_byte_identical_comparator': True,
        'comparator_diagnostic_sha256': canon_sha,
        'command_live_rust': 'cd amphora-viscosity-score && cargo run --quiet --example kd_live_runtime_parity_probe',
        'command_comparator': 'cd amphora-viscosity-score/evidence/audit/kd-live-runtime-parity-v1 && python3 run_kd_live_parity_check.py diagnostic.canonical.json',
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
ptype = 'application/vnd.amphora.viscosity-score-kd-live-runtime-parity+json'
sig = eval_sk.sign(pae(ptype, body))
envelope = {'payload': base64.standard_b64encode(body).decode(), 'payloadType': ptype,
            'signatures': [{'keyid': eval_key_id, 'sig': base64.standard_b64encode(sig).decode()}]}
receipt = {'evaluator_key_id': eval_key_id, 'evaluator_public_key_hex': eval_pub_hex,
           'reviewer_public_key_hex': rev_pub_hex, 'signature': envelope}
out = EV / 'kd-live-runtime-parity-receipt.v1.dsse.json'
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
