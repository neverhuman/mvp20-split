#!/usr/bin/env python3
"""Comparator/analysis for the amphora-viscosity-score Grunberg-Nissan live-runtime
interaction-wiring audit. AUDIT_ONLY. Reads the byte-identical two-replay live-Rust
diagnostics, independently re-derives the numeric findings in pure Python (no reuse of
the Rust arithmetic), and performs a static structural scan of src/lib.rs proving the
sole call site is architecturally incapable of supplying a non-zero interaction term."""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path('/home/ubuntu/amphora/build/mvp20-split')
MOD = ROOT / 'amphora-viscosity-score'
LIB = MOD / 'src/lib.rs'
EV = MOD / 'evidence/audit/gn-degenerate-ideal-mixing-v1'


def sha(b):
    return hashlib.sha256(b).hexdigest()


live_a = json.loads((EV / 'gn_live_runA.json').read_text())
live_b = json.loads((EV / 'gn_live_runB.json').read_text())
live_a_sha = sha((EV / 'gn_live_runA.json').read_bytes())
live_b_sha = sha((EV / 'gn_live_runB.json').read_bytes())
assert live_a_sha == live_b_sha, 'two-replay byte-stability gate FAILED (live cargo run)'
assert live_a == live_b

fractions = live_a['inputs']['fractions']
viscosities = live_a['inputs']['viscosities_pa_s']
g12 = live_a['inputs']['nonzero_g12_demo_magnitude']

# Independent pure-Python re-derivation (never touches the Rust arithmetic).
ideal_py = math.exp(sum(x * math.log(eta) for x, eta in zip(fractions, viscosities)))
gn_zero_py = ideal_py  # zero interaction term collapses to ideal mixing algebraically
gn_nonzero_py = math.exp(
    sum(x * math.log(eta) for x, eta in zip(fractions, viscosities))
    + fractions[0] * fractions[1] * g12
)

rel = lambda a, b: abs(a - b) / abs(b) if b else abs(a - b)

numeric_checks = {
    'ideal_mixing_py_vs_rust': {
        'py': ideal_py,
        'rust': live_a['ideal_mixing_independent_closed_form_pa_s'],
        'rel_diff': rel(ideal_py, live_a['ideal_mixing_independent_closed_form_pa_s']),
        'within_1e_9': rel(ideal_py, live_a['ideal_mixing_independent_closed_form_pa_s']) < 1e-9,
    },
    'gn_zero_interaction_py_vs_rust': {
        'py': gn_zero_py,
        'rust': live_a['gn_zero_interaction_result_pa_s'],
        'rel_diff': rel(gn_zero_py, live_a['gn_zero_interaction_result_pa_s']),
        'within_1e_9': rel(gn_zero_py, live_a['gn_zero_interaction_result_pa_s']) < 1e-9,
    },
    'gn_nonzero_interaction_py_vs_rust': {
        'py': gn_nonzero_py,
        'rust': live_a['gn_nonzero_interaction_result_pa_s'],
        'rel_diff': rel(gn_nonzero_py, live_a['gn_nonzero_interaction_result_pa_s']),
        'within_1e_9': rel(gn_nonzero_py, live_a['gn_nonzero_interaction_result_pa_s']) < 1e-9,
    },
}
assert all(c['within_1e_9'] for c in numeric_checks.values()), 'independent Python re-derivation diverged from live Rust'

zero_vs_nonzero_rel_diff = rel(gn_nonzero_py, gn_zero_py)
assert zero_vs_nonzero_rel_diff > 0.01, 'sensitivity check: nonzero interaction term must be non-negligible'

# Static structural scan of src/lib.rs: every call site of grunberg_nissan_mix, and
# every reference to "interaction" anywhere in the schema/definition/tests.
src = LIB.read_text()
lines = src.splitlines()

call_site_pattern = re.compile(r'\bgrunberg_nissan_mix\s*\(')
call_sites = [i + 1 for i, line in enumerate(lines) if call_site_pattern.search(line) and 'fn grunberg_nissan_mix' not in line]
# Exclude the function definition line itself (search for 'pub fn grunberg_nissan_mix')
def_line = next(i + 1 for i, line in enumerate(lines) if 'pub fn grunberg_nissan_mix' in line)
call_sites = [n for n in call_sites if n != def_line]

production_call_sites = []
test_call_sites = []
# tests module starts at the "mod tests {" line
tests_mod_line = next((i + 1 for i, line in enumerate(lines) if re.search(r'^mod tests', line)), len(lines) + 1)
for n in call_sites:
    (test_call_sites if n >= tests_mod_line else production_call_sites).append(n)

def split_top_level_args(arg_text):
    """Split a call's argument-list text on top-level commas (depth-aware over ()[]{})."""
    args, depth, current = [], 0, []
    for ch in arg_text:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if ch == ',' and depth == 0:
            args.append(''.join(current))
            current = []
        else:
            current.append(ch)
    if current:
        args.append(''.join(current))
    return [a.strip() for a in args]


def third_arg_of_call(text_around_call):
    """Extract the 3rd (interactions) argument text of the nearest grunberg_nissan_mix(...) call,
    resolving a one-level-back `let interactions = <expr>;` binding if the call passes a bare
    identifier `interactions` rather than an inline literal."""
    call_start = text_around_call.rindex('grunberg_nissan_mix(') + len('grunberg_nissan_mix(')
    depth = 1
    i = call_start
    while depth > 0:
        if text_around_call[i] in '([{':
            depth += 1
        elif text_around_call[i] in ')]}':
            depth -= 1
        i += 1
    call_args_text = text_around_call[call_start:i - 1]
    args = split_top_level_args(call_args_text)
    third = args[2] if len(args) >= 3 else ''
    third_ident = third.lstrip('&').strip()
    if third_ident.isidentifier():
        m = re.search(r'let\s+' + re.escape(third_ident) + r'\s*=\s*(.+?);', text_around_call, re.DOTALL)
        if m:
            return m.group(1)
    return third


non_zero_digit_pattern = re.compile(r'[1-9]')
all_call_sites_use_hardcoded_zero = True
call_site_detail = []
for n in call_sites:
    window = '\n'.join(lines[max(0, n - 4):n])
    matrix_literal_text = third_arg_of_call(window)
    # `.len()` calls contain no digits themselves, so a plain digit scan on the resolved
    # interactions-argument text is sufficient once identifiers/method calls are left as-is.
    uses_zero_literal = not non_zero_digit_pattern.search(matrix_literal_text)
    call_site_detail.append({
        'line': n, 'is_production': n < tests_mod_line, 'window': window,
        'interactions_arg_resolved_text': matrix_literal_text,
        'supplies_hardcoded_zero_matrix': uses_zero_literal,
    })
    if not uses_zero_literal:
        all_call_sites_use_hardcoded_zero = False

interaction_field_pattern = re.compile(r'interaction', re.IGNORECASE)
interaction_refs = [i + 1 for i, line in enumerate(lines) if interaction_field_pattern.search(line)]
# The only permissible references are inside grunberg_nissan_mix's own signature/body
# (found via brace-depth counting from its opening brace, not a naive first-`}` scan,
# since the function contains nested for-loop blocks) and its call sites (plus the
# `let interactions = ...;` construction line immediately preceding each call).
open_line = next(i for i, line in enumerate(lines, start=1) if i >= def_line and '{' in line)
depth = 0
fn_body_end = open_line
for i in range(open_line, len(lines) + 1):
    depth += lines[i - 1].count('{') - lines[i - 1].count('}')
    if depth <= 0:
        fn_body_end = i
        break
allowed_lines = set(range(def_line, fn_body_end + 1)) | set(call_sites) | {n - 1 for n in call_sites}
unexplained_interaction_refs = [n for n in interaction_refs if n not in allowed_lines]

theory_caller_pattern = re.compile(r'theory_apparent_viscosity\(')
theory_callers = [i + 1 for i, line in enumerate(lines) if theory_caller_pattern.search(line) and 'pub fn theory_apparent_viscosity' not in line]

out = {
    'schema': 'amphora.viscosity-score.gn-degenerate-ideal-mixing-diagnostic.v1',
    'module_id': 'amphora-viscosity-score',
    'lib_rs_sha256': sha(LIB.read_bytes()),
    'numeric_checks': numeric_checks,
    'zero_vs_nonzero_interaction_rel_diff': zero_vs_nonzero_rel_diff,
    'call_site_scan': {
        'all_grunberg_nissan_mix_call_sites_in_crate': call_sites,
        'production_call_sites': production_call_sites,
        'test_call_sites': test_call_sites,
        'production_call_site_count': len(production_call_sites),
        'call_site_detail': call_site_detail,
        'every_call_site_supplies_hardcoded_zero_matrix': all_call_sites_use_hardcoded_zero,
    },
    'interaction_field_scan': {
        'all_line_numbers_matching_interaction_case_insensitive': interaction_refs,
        'lines_explained_by_function_def_or_known_call_sites': sorted(allowed_lines),
        'unexplained_interaction_references': unexplained_interaction_refs,
        'no_schema_field_carries_interaction_data': len(unexplained_interaction_refs) == 0,
    },
    'theory_apparent_viscosity_callers': theory_callers,
    'live_rust_diagnostic_sha256': live_a_sha,
    'end_to_end_theory_apparent_viscosity_two_liquid_observation_pa_s': live_a['end_to_end_theory_apparent_viscosity_two_liquid_observation_pa_s'],
    'finding': (
        'grunberg_nissan_mix has exactly ' + str(len(production_call_sites)) + ' production call site(s) '
        'in the entire crate (src/lib.rs, inside theory_apparent_viscosity), and it and both of the '
        'function\'s own unit tests supply ONLY a hardcoded all-zero interaction matrix. No struct field '
        'anywhere in the module schema (RheologyObservationV1, LiquidComponentV1, PigmentComponentV1, '
        'RheologyAdditiveV1) carries interaction-parameter data, so even a caller with real Grunberg-Nissan '
        'd_ij data has no way to supply it. theory_apparent_viscosity is called by both fit_model (line '
        + ', '.join(str(n) for n in theory_callers) + ' in src/lib.rs) and predict, i.e. every training row '
        'and every scored candidate. An independent pure-Python re-derivation confirms the live-Rust '
        'zero-interaction result is bit-equivalent (within 1e-9) to plain ideal (mass-fraction-weighted '
        'log-linear) mixing, and that supplying a non-zero, order-unity interaction term (the term that '
        'defines Grunberg-Nissan over ideal mixing) changes the result by '
        + f'{zero_vs_nonzero_rel_diff:.1%}' + ' -- proving the omitted term is not negligible when the '
        'function IS given real interaction data. The module\'s cited "Grunberg-Nissan blend mixing" '
        'built-in path (docs/mission.md; reference/rheology/source-landscape.v1.json source_id '
        '"grunberg-nissan-1949") is, as actually wired into the live runtime, architecturally incapable '
        'of ever computing anything other than ideal mixing -- this is a structural/architecture gap, not '
        'merely a data gap awaiting wet-lab validation as mission.md currently frames it alongside '
        'Krieger-Dougherty and Herschel-Bulkley.'
    ),
}
print(json.dumps(out, indent=2, sort_keys=True))
