#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Arrhenius fixture source-provenance
audit. AUDIT_ONLY. Does not modify the master manifest, does not modify any existing
signed receipt or KPI, does not promote any KPI or flip module phase/scientific_readiness."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
EV = MOD / 'evidence/audit/arrhenius-fixture-source-provenance-v1'
SEED_DIR = Path.home() / '.local/share/amphora/phase0/keys'
EVAL_SEED = SEED_DIR / 'evaluator.ed25519.seed'
REVIEWER_SEED = SEED_DIR / 'internal-reviewer.ed25519.seed'
TRUST = ROOT / 'config/phase0-trust-store.v1.json'

FIRE_ID = '20260818T130001-3750098-a997b91711f7'


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

harness_path = EV / 'run_arrhenius_source_provenance_probe.py'
harness_sha = sha(harness_path.read_bytes())
pdf_sha = sha((EV / 'glycerinWaterViscosity_Dorsey_mirror.pdf').read_bytes())

kpi_path = MOD / 'evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json'
kpi_sha = sha(kpi_path.read_bytes())
assert kpi_sha == diag['kpi_under_attack_sha256'], 'kpi sha mismatch vs diagnostic'

fixture_path = MOD / 'reference/phase0-viscosity-known-answer.v1.json'
fixture_sha = sha(fixture_path.read_bytes())
assert fixture_sha == diag['fixture_sha256'], 'fixture sha mismatch vs diagnostic'

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

a1 = diag['angle_1_offline_fit_reproducibility']
a2 = diag['angle_2_external_data_provenance']
pc1 = diag['positive_control_1_fabricated_ea']
pc2 = diag['positive_control_2_wrong_column']

body_obj = {
    'schema': 'amphora.viscosity-score.arrhenius-fixture-source-provenance-receipt.v1',
    'receipt_id': 'arrhenius-fixture-source-provenance-v1',
    'module_id': 'amphora-viscosity-score',
    'authority': 'AUDIT_ONLY',
    'authority_ceiling': 'EVIDENCE_ONLY',
    'phase': 'PRE_PHASE_0',
    'scientific_success_required_for_phase0': False,
    'date': '2026-08-18',
    'fire_id': FIRE_ID,
    'generated_on_host': 'xbabe2 (compute, deterministic python re-derivation); xbabe1 (orchestration, WebSearch/WebFetch source discovery)',
    'promotes_authority': False,
    'flips_scientific_readiness': False,
    'human_review_performed': False,
    'organizational_independence_asserted': False,
    'modifies_manifest': False,
    'modifies_locked_dataset': False,
    'modifies_signed_phase0_kpi': False,
    'campaign_item_id': '',
    'claim_under_attack': (
        'evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json (sha256 ' + kpi_sha + ') headline '
        'PASS gates -- arrhenius_mape_within_training_range (observed 1.26%, ceiling 5%), '
        'arrhenius_over_constant_baseline_lift (observed +64.1pp, floor 20pp), '
        'held_out_temperature_extrapolation_mape (observed 0.49%, ceiling 8%), '
        'per_solvent_minimum_prediction_quality_rate (observed 1.0, floor 0.85), and the '
        'observational r_squared_arrhenius_minimum (0.9904) -- read together with docs/mission.md '
        'prose describing the underlying reference/phase0-viscosity-known-answer.v1.json fixture '
        '(sha256 ' + fixture_sha + ') as a self-authored compilation of published CRC Handbook / '
        'NIST WebBook / Yaws\' Handbook values with per-solvent activation energies "fitted offline '
        'via numpy linear regression" -- amount to a standing claim that these headline numbers '
        'reflect the model\'s true accuracy against correctly-transcribed published reference data, '
        'and that the baked-in "offline fit" description is faithful. This is the module\'s only '
        'benchmark that already runs the live compiled arrhenius_viscosity primitive end-to-end '
        '(tests/viscosity_phase0_kpi.rs), so unlike the KD/HB live-runtime-parity fires the closed-'
        'form arithmetic itself was never in question here; this attack instead targets the fixture '
        'inputs that arithmetic is fed.'
    ),
    'attack_description': (
        'Two independent, previously-untested angles on the fixture, run via a deterministic pure-'
        'Python harness (no RNG, no floating-point-order ambiguity) committed at '
        'evidence/audit/arrhenius-fixture-source-provenance-v1/run_arrhenius_source_provenance_probe.py '
        '(sha256 ' + harness_sha + '), replayed twice with byte-identical output (sha256 ' + canon_sha + '): '
        '(1) OFFLINE-FIT REPRODUCIBILITY -- independently re-ran the exact linear regression '
        '(ln(eta) vs 1/T over the fixture\'s own {20,40,60}C points) for all 25 solvents and diffed '
        'against the fixture\'s baked-in fitted_activation_energy_j_mol / fitted_r_squared, the same '
        'class of "verbatim re-derivation" check that already found real divergences elsewhere in '
        'this module (kd-live-runtime-parity-v1, hb-live-runtime-parity-v1, both CLAIM_REFUTED). '
        '(2) EXTERNAL DATA-PROVENANCE CROSS-CHECK -- fetched, this fire, a widely-cited independent '
        'compilation of glycerol dynamic viscosity (Segur & Oberstar 1951, Ind. Eng. Chem. 43(9):2117, '
        'as reproduced at web.cecs.pdx.edu/~gerry/class/EAS361/lab/pdf/glycerinWaterViscosity_Dorsey.pdf, '
        'mirrored at evidence/audit/arrhenius-fixture-source-provenance-v1/glycerinWaterViscosity_Dorsey_mirror.pdf, '
        'sha256 ' + pdf_sha + ') -- the same class of published physical-property table (CRC/NIST/GPA-'
        'type) the fixture itself claims to draw from, and the same primary source class already used '
        'by the sibling arrhenius-extrapolation-domain-gap-v1 fire -- and diffed the fixture\'s own raw '
        'viscosity_mpas_{20,30,40,60}c entries for glycerol (chosen as the highest-Ea, most temperature-'
        'sensitive of the 25 solvents) against it, then re-ran the full KPI computation with the '
        'externally-sourced numbers substituted in to see whether any gate flips.'
    ),
    'method_fidelity_note': (
        'The KPI harness itself (tests/viscosity_phase0_kpi.rs) already calls the live compiled '
        'arrhenius_viscosity primitive directly, so this probe reimplements only the closed-form '
        'Arrhenius equation and the aggregate metric definitions (byte-for-byte matching the Rust '
        'logic read from tests/viscosity_phase0_kpi.rs) in order to re-run them against alternate '
        'input data the Rust harness cannot swap in without a code change; this is a controlled-'
        'input sensitivity analysis, not a claim of live-runtime execution.'
    ),
    'findings': {
        'angle_1_offline_fit_reproducibility': {
            'max_ea_relative_error': a1['max_ea_relative_error'],
            'max_r2_absolute_error': a1['max_r2_absolute_error'],
            'n_solvents_checked': a1['n_solvents'],
            'interpretation': a1['interpretation'],
        },
        'angle_2_external_data_provenance': {
            'solvent_checked': a2['solvent_checked'],
            'reason_selected': a2['reason_selected'],
            'per_temperature_diff': a2['per_temperature'],
            'note': (
                '20C and 60C match the independent Segur-Oberstar/Dow table almost exactly '
                '(+0.142%, +0.000%); 30C and 40C are both ~1.8% higher in the fixture than in this '
                'independent table (+1.797%, +1.761%) -- a real, reproducible, non-random-looking '
                'discrepancy against the fixture\'s cited CRC Handbook source. This is disclosed as '
                'a genuine minor data-provenance finding; see gate-sensitivity result below for '
                'whether it changes the standing claim.'
            ),
            'gate_sensitivity_result': {
                'any_gate_flip_vs_original': a2['any_gate_flip_vs_original'],
                'original_report': diag['original_report'],
                'corrected_report_using_independent_source': a2['corrected_report'],
                'deltas': a2['deltas_vs_original'],
            },
        },
    },
    'positive_control': {
        'planted_defect': pc1['planted_defect'] + ' | AND | ' + pc2['planted_defect'],
        'how_planted': pc1['how_planted'] + ' | AND | ' + pc2['how_planted'],
        'detected': bool(pc1['detected'] and pc2['detected']),
        'evidence': (
            'PC1 (fabricated offline fit): ' + str(pc1['evidence']) + '. '
            'PC2 (realistic wrong-column table-misread, same hazard class as the Amorim-2021 HB '
            'fire): substituting the wrong glycerol column flips BOTH '
            'arrhenius_mape_within_training_range (' +
            str(diag['positive_control_2_wrong_column']['evidence']['arrhenius_mape_within_training_range']) +
            ' vs ceiling 0.05, gate=' +
            str(diag['positive_control_2_wrong_column']['evidence']['gates']['arrhenius_mape_within_training_range']) +
            ') and held_out_temperature_extrapolation_mape (' +
            str(diag['positive_control_2_wrong_column']['evidence']['held_out_temperature_extrapolation_mape']) +
            ' vs ceiling 0.08, gate=' +
            str(diag['positive_control_2_wrong_column']['evidence']['gates']['held_out_temperature_extrapolation_mape']) +
            ') to FAIL, proving the harness has real power to detect a defect of the kind this attack '
            'exists to catch -- not just a trivially different one.'
        ),
    },
    'refutation_criterion': (
        'The claim under attack would be REFUTED by observing EITHER (a) the offline-fit '
        'reproducibility check finding a baked-in Ea/R2 that does not match a from-scratch '
        'regression on the fixture\'s own raw numbers (evidence the "numpy fit" description is '
        'false, mirroring the KD/HB live-runtime-parity findings), OR (b) substituting '
        'independently re-sourced raw viscosity data for any solvent flipping any KPI gate from '
        'PASS to FAIL. It would SURVIVE if the offline fit reproduces exactly AND no gate flips '
        'under the externally-verified data.'
    ),
    'observed': (
        'Neither refuting condition occurred. (a) max Ea relative error across all 25 solvents = ' +
        '{:.2e}'.format(a1['max_ea_relative_error']) + ' and max R2 absolute error = ' +
        '{:.2e}'.format(a1['max_r2_absolute_error']) + ' -- floating-point-precision reproduction, '
        'not a mismatch. (b) substituting the independently-sourced Segur-Oberstar/Dow glycerol '
        'values (which DO differ from the fixture by up to 1.8% at 30C/40C) changes '
        'arrhenius_mape_within_training_range from 1.2595% to 1.2960% (ceiling 5%) and '
        'held_out_temperature_extrapolation_mape from 0.4897% to 0.5633% (ceiling 8%) -- both stay '
        'comfortably PASS, with wide headroom, and no gate flips.'
    ),
    'verdict': diag['verdict'],
    'verdict_scope': (
        'SURVIVED narrowly on the two angles tested: the fixture\'s baked-in offline-fit values are '
        'a faithful arithmetic reproduction of its own raw numbers (not fabricated), and the one '
        'real data-provenance discrepancy this fire could locate (glycerol 30C/40C ~1.8% high vs an '
        'independent Segur-Oberstar/Dow source) is too small to move any gate. This does NOT certify '
        'that all 25 solvents\' raw published values are individually correct against their cited '
        'CRC/NIST/Yaws sources -- only glycerol was externally cross-checked this fire, chosen as the '
        'single highest-leverage (highest-Ea, most temperature-sensitive) solvent; the other 24 '
        'remain unverified against independent sources. It also does not resolve the still-open '
        'glycerol-source discrepancy itself, which is disclosed here but not investigated further '
        '(e.g. which CRC 100th-ed. printing/rounding produced 623.0/289.0 mPa*s at 30C/40C is '
        'unknown) -- a candidate follow-up for a future fire.'
    ),
    'kpi_under_attack_sha256': kpi_sha,
    'fixture_under_attack_sha256': fixture_sha,
    'harness_sha256': {'run_arrhenius_source_provenance_probe.py': harness_sha},
    'external_source_mirror_sha256': {'glycerinWaterViscosity_Dorsey_mirror.pdf': pdf_sha},
    'reproducibility': {
        'two_replay_byte_identical': True,
        'diagnostic_sha256': canon_sha,
        'command': 'cd amphora-viscosity-score/evidence/audit/arrhenius-fixture-source-provenance-v1 && python3 run_arrhenius_source_provenance_probe.py',
        'determinism': 'pure deterministic floating-point closed-form arithmetic, no RNG, no network I/O at run time',
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
ptype = 'application/vnd.amphora.viscosity-score-arrhenius-fixture-source-provenance+json'
sig = eval_sk.sign(pae(ptype, body))
envelope = {'payload': base64.standard_b64encode(body).decode(), 'payloadType': ptype,
            'signatures': [{'keyid': eval_key_id, 'sig': base64.standard_b64encode(sig).decode()}]}
receipt = {'evaluator_key_id': eval_key_id, 'evaluator_public_key_hex': eval_pub_hex,
           'reviewer_public_key_hex': rev_pub_hex, 'signature': envelope}
out = EV / 'arrhenius-fixture-source-provenance-receipt.v1.dsse.json'
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
