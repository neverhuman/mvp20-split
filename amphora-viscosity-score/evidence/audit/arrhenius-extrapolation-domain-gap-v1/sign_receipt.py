#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Arrhenius extrapolation-domain-gap
audit. AUDIT_ONLY. Does not modify the master manifest, does not modify any existing
signed receipt or KPI, does not promote any KPI or flip module phase/scientific_readiness."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
EV = MOD / 'evidence/audit/arrhenius-extrapolation-domain-gap-v1'
SEED_DIR = Path.home() / '.local/share/amphora/phase0/keys'
EVAL_SEED = SEED_DIR / 'evaluator.ed25519.seed'
REVIEWER_SEED = SEED_DIR / 'internal-reviewer.ed25519.seed'
TRUST = ROOT / 'config/phase0-trust-store.v1.json'

FIRE_ID = '20260814T130001-2255528-544555cc0ef7'


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
assert canon_sha == sha(runB), 'two-replay byte-stability gate FAILED'
diag = json.loads(canon)

harness_path = EV / 'arrhenius_extrapolation_probe.rs'
harness_sha = sha(harness_path.read_bytes())
pdf_sha = sha((EV / 'glycerine-producers-association-1963-dorsey-viscosity-table-source.pdf').read_bytes())

kpi_path = MOD / 'evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json'
kpi_sha = sha(kpi_path.read_bytes())

water = diag['water']
glycerol = diag['glycerol']

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
    'schema': 'amphora.viscosity-score.arrhenius-extrapolation-domain-gap-receipt.v1',
    'receipt_id': 'arrhenius-extrapolation-domain-gap-v1',
    'module_id': 'amphora-viscosity-score',
    'authority': 'AUDIT_ONLY',
    'authority_ceiling': 'EVIDENCE_ONLY',
    'phase': 'PRE_PHASE_0',
    'scientific_success_required_for_phase0': False,
    'date': '2026-08-14',
    'fire_id': FIRE_ID,
    'generated_on_host': 'xbabe2 (compute, live cargo run of the compiled crate); xbabe1 (orchestration, WebSearch/WebFetch source discovery)',
    'promotes_authority': False,
    'flips_scientific_readiness': False,
    'human_review_performed': False,
    'organizational_independence_asserted': False,
    'modifies_manifest': False,
    'modifies_locked_dataset': False,
    'modifies_signed_phase0_kpi': False,
    'campaign_item_id': '',
    'claim_under_attack': (
        'evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json (sha256 ' + kpi_sha + ') gates '
        '`applicability_domain_fail_closed_rate` (observed 1.0, floor 1.0, PASSED) and '
        '`held_out_temperature_extrapolation_mape` (observed 0.49% at 30C, ceiling 8%, PASSED) '
        '-- read together with docs/mission.md prose describing these as validating the model '
        'against "held-out temperature extrapolation" -- amount to a standing claim that the '
        '`arrhenius_viscosity` primitive (src/lib.rs:1147) is safe to call, or has been validated, '
        'outside its per-solvent [20,60]C fitting window, and that its range guard '
        '(finite_between(-273.14, 500.0)) constitutes an adequate applicability-domain check.'
    ),
    'attack_description': (
        'Live-runtime (real compiled Rust, not a reimplementation) domain-extrapolation probe. '
        'Built a new cargo example, examples/arrhenius_extrapolation_probe.rs (byte-identical copy '
        'committed at evidence/audit/arrhenius-extrapolation-domain-gap-v1/arrhenius_extrapolation_probe.rs, '
        'sha256 ' + harness_sha + '), that calls the live `arrhenius_viscosity` function using the '
        'exact same calling convention as the module\'s own KPI test (tests/viscosity_phase0_kpi.rs: '
        '`arrhenius_viscosity(eta_ref_pas, 25.0, t_c, ea)`) and the KPI\'s own committed fitted '
        'parameters for water and glycerol -- both members of the fixture\'s own 25-solvent set -- '
        'read at runtime from the committed KPI file and asserted byte-identical to the constants '
        'baked into the probe (assert_kpi_params_match). Evaluated at T in {0,10,...,100}C in 10C '
        'steps against an independently sourced published table: Segur & Oberstar (1951, Ind. Eng. '
        'Chem. 43(9):2117-2120) as compiled in "Physical Properties of Glycerine and Its Solutions", '
        'Glycerine Producers\' Association (1963) -- the 100 wt% (pure glycerine) and 0 wt% (pure '
        'water, itself footnoted in that table to N.E. Dorsey 1940) columns -- fetched this fire from '
        'a public course mirror (sha256 ' + pdf_sha + '). This is the same class of compiled physical-'
        'property reference table (CRC/NIST/GPA-type) the fixture itself claims to draw from, applied '
        'at 5 additional temperature points per solvent that the fixture never tests. Two independent '
        '`cargo run --example` executions produced byte-identical diagnostics (sha256 ' + canon_sha + '), '
        'satisfying the two-replay determinism gate.'
    ),
    'method_fidelity_note': (
        'Calls the live compiled arrhenius_viscosity primitive directly (amphora_viscosity_score::'
        'arrhenius_viscosity), the same public function the KPI benchmark and any downstream caller '
        'would use -- this is a real-runtime probe, not a Python/CPython re-derivation.'
    ),
    'findings': {
        'held_out_temperature_extrapolation_mape_is_mislabeled': (
            'The KPI\'s own test file (tests/viscosity_phase0_kpi.rs) fits each solvent on '
            '{20,40,60}C and evaluates "held_out_temperature_extrapolation_mape" at 30C -- a point '
            'strictly INSIDE the [20,60]C fitted span and between two of the three fitted anchor '
            'points (20 and 40). This is interpolation, not extrapolation. No point in the KPI\'s own '
            'gate suite lies outside [20,60]C. The KPI has never been evaluated at a genuine '
            'out-of-fitted-window temperature.'
        ),
        'range_guard_is_a_physical_plausibility_bound_not_a_domain_of_validity_bound': (
            'src/lib.rs:1147-1157: the only input check on temperature_c/reference_temperature_c is '
            'finite_between(x, -273.14, 500.0) -- i.e. "above absolute zero, below 500C". This guard '
            'accepted every single out-of-fitted-window probe call in this attack '
            '(range_guard_ever_rejected_an_out_of_window_call: false for both solvents, ' +
            str(water['out_of_window_probe_count']) + '+' + str(glycerol['out_of_window_probe_count']) +
            ' = ' + str(water['out_of_window_probe_count'] + glycerol['out_of_window_probe_count']) +
            ' out-of-window calls, 0 rejected).'
        ),
        'water_out_of_window_probe': {
            'worst_abs_pct_err_outside_20_60c': water['worst_out_of_fitted_window_abs_pct_err'],
            'breaches_of_10pct_quality_floor': water['out_of_window_breaches_10pct_quality_floor'],
            'of_probes': water['out_of_window_probe_count'],
            'worst_abs_pct_err_inside_20_60c_for_contrast': water['worst_in_fitted_window_abs_pct_err'],
        },
        'glycerol_out_of_window_probe': {
            'worst_abs_pct_err_outside_20_60c': glycerol['worst_out_of_fitted_window_abs_pct_err'],
            'breaches_of_10pct_quality_floor': glycerol['out_of_window_breaches_10pct_quality_floor'],
            'of_probes': glycerol['out_of_window_probe_count'],
            'worst_abs_pct_err_inside_20_60c_for_contrast': glycerol['worst_in_fitted_window_abs_pct_err'],
            'interpretation': (
                'Glycerol is a well-documented glass-forming, strongly hydrogen-bonded liquid whose '
                'viscosity-temperature curve is known in the physical-chemistry literature to be '
                'super-Arrhenius (better described by Vogel-Fulcher-Tammann than by a single-Ea '
                'Arrhenius law) -- even the module\'s own sibling benchmark '
                '(benchmarks/vft-arrhenius-adequacy-v1) exists to test exactly this class of question '
                'for a related viscosity endpoint. Even ONE of glycerol\'s three in-window fitting '
                'points (40C and 50C, both inside [20,60]C) already shows 7.2% and 7.6% residual '
                'against this same published source despite being fit on 20/40/60C directly -- '
                'evidence of real curvature the straight-line Arrhenius fit cannot capture even '
                'in-sample. Immediately outside the fitted window this compounds to a worst-case '
                '42.8% error at 100C, breaching the module\'s own +/-10% per-solvent quality floor '
                'by a factor of ~4.3, with the function returning Ok(_) (a confident, silent, '
                'deterministic number) rather than any error or warning.'
            ),
        },
        'contrast_with_water': (
            'Water -- much weaker hydrogen-bond-network curvature over this range -- breaches the '
            '10% floor only twice out of 6 out-of-window probes (worst 11.8% at the 100C extreme), '
            'versus glycerol breaching all 6 of 6 (worst 42.8%). This rules out a generic '
            '"extrapolation always fails a little" objection: the failure magnitude tracks the '
            'known physical-chemistry distinction between a mildly-curved and a strongly glass-'
            'forming liquid, which is exactly the class of edge-of-envelope failure a domain-of-'
            'validity guard should catch and the current [-273.14,500]C guard cannot.'
        ),
    },
    'positive_control': 'not_applicable_to_this_verdict',
    'positive_control_note': (
        'This receipt reports CLAIM_REFUTED, which per protocol carries its own evidence and does '
        'not require a positive control (that requirement applies to CLAIM_SURVIVED verdicts).'
    ),
    'refutation_criterion': (
        'The claim under attack -- that the KPI\'s applicability_domain_fail_closed_rate=1.0 and '
        'held_out_temperature_extrapolation_mape gates demonstrate the model is validated, or safe '
        'to call, outside its [20,60]C per-solvent fitting window -- would be REFUTED by observing '
        'BOTH (a) the code\'s range guard accepting calls at temperatures genuinely outside the '
        'fitted window (rather than rejecting them), AND (b) at least one such accepted out-of-'
        'window call producing an error against an independently sourced published value that '
        'exceeds the module\'s own +/-10% per-solvent quality floor (the same floor the in-window '
        '`per_solvent_minimum_prediction_quality_rate` KPI gate enforces at 0.85 fraction). It would '
        'SURVIVE if the range guard rejected out-of-window calls, or if all out-of-window predictions '
        'stayed within the module\'s own accuracy floor.'
    ),
    'observed': (
        'Both refuting conditions occurred. The range guard accepted all ' +
        str(water['out_of_window_probe_count'] + glycerol['out_of_window_probe_count']) +
        ' out-of-fitted-window calls across both solvents (0 rejected). 8 of those 12 calls (' +
        str(water['out_of_window_breaches_10pct_quality_floor']) + '/6 water, ' +
        str(glycerol['out_of_window_breaches_10pct_quality_floor']) + '/6 glycerol) breached the '
        'module\'s own 10% per-solvent quality floor against an independently sourced published '
        'table, with glycerol reaching 42.8% error at 100C -- a temperature squarely inside the '
        'code\'s accepted range and squarely outside the temperature range any of the KPI\'s existing '
        'gates ever probe.'
    ),
    'verdict': 'CLAIM_REFUTED',
    'verdict_scope': (
        'REFUTED narrowly: the specific claim that the KPI\'s existing applicability-domain and '
        '"held-out extrapolation" gates validate, or that the code\'s range guard protects against, '
        'genuine out-of-fitted-window use of arrhenius_viscosity. This does NOT refute the in-window '
        '(20-60C) Arrhenius benchmark itself, whose own numbers (1.26% MAPE, R^2 0.9904 worst-case) '
        'are reproduced by this same probe for the in-window points and are left standing. It also '
        'does not claim glycerol\'s viscosity is generally unmeasurable by any Arrhenius-type '
        'model (a proper VFT fit could plausibly do much better across the full 0-100C span); the '
        'refutation is specifically about the CURRENT single-Ea implementation\'s silent behavior '
        'outside its fitted window and the current KPI\'s failure to test for it.'
    ),
    'recommended_repair': (
        'Either (a) narrow arrhenius_viscosity\'s accepted temperature_c range to a per-call or '
        'per-solvent-documented fitted window (or add an explicit applicability-domain flag/warning '
        'output) rather than the current absolute-physical-plausibility-only guard, or (b) add a '
        'genuine out-of-window extrapolation gate to the KPI (e.g. at 0C and 80-100C, both physically '
        'reachable in coating cure/application scenarios) so any future non-Arrhenius solvent is '
        'caught by construction rather than by accident. Not performed in this fire (AUDIT_ONLY, no '
        'src/lib.rs behavior change made or required to land this finding).',
    ),
    'published_source': {
        'citation': 'Segur, J.B. & Oberstar, H.E. (1951) "Viscosity of Glycerol and Its Aqueous '
                    'Solutions", Industrial and Engineering Chemistry 43(9):2117-2120, as compiled '
                    'in "Physical Properties of Glycerine and Its Solutions", Glycerine Producers\' '
                    'Association (1963); water column footnoted in the same table to N.E. Dorsey, '
                    '"Properties of Ordinary Water-Substance", p.184, New York (1940).',
        'mirror_url_fetched_this_fire': 'https://web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf',
        'mirror_sha256': pdf_sha,
        'rights_position': (
            'A standard compiled physical-property reference table (numeric physical constants), '
            'the same category of fact-only compilation as the CRC Handbook / NIST WebBook / Yaws '
            'tables the fixture itself is built from -- not a creative work subject to the same '
            'copyright concerns as a journal figure/dataset. No values were bulk-extracted beyond '
            'the 22 (11 temperatures x 2 solvents) numbers used directly in this diagnostic, all '
            'disclosed inline in the harness source and in this receipt\'s findings block.',
        ),
    },
    'kpi_under_attack_sha256': kpi_sha,
    'harness_sha256': {'arrhenius_extrapolation_probe.rs': harness_sha},
    'reproducibility': {
        'two_replay_byte_identical': True,
        'diagnostic_sha256': canon_sha,
        'command': 'cd amphora-viscosity-score && cargo run --quiet --example arrhenius_extrapolation_probe',
        'determinism': 'pure deterministic floating-point Arrhenius closed form, no RNG, no network I/O at run time',
    },
    'full_diagnostic_row_data': diag,
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
ptype = 'application/vnd.amphora.viscosity-score-arrhenius-extrapolation-domain-gap+json'
sig = eval_sk.sign(pae(ptype, body))
envelope = {'payload': base64.standard_b64encode(body).decode(), 'payloadType': ptype,
            'signatures': [{'keyid': eval_key_id, 'sig': base64.standard_b64encode(sig).decode()}]}
receipt = {'evaluator_key_id': eval_key_id, 'evaluator_public_key_hex': eval_pub_hex,
           'reviewer_public_key_hex': rev_pub_hex, 'signature': envelope}
out = EV / 'arrhenius-extrapolation-domain-gap-receipt.v1.dsse.json'
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
