"""Validate a candid assessment; this profile cannot declare an investment gate met."""
from .core import bounded_read, closed, require, strict_json


def check_decisions(path):
    value = strict_json(bounded_read(path))
    closed(value, {'format', 'assessment_scope', 'gates'})
    require(value['format'] == 'amphora-investment-assessment.v2' and
            isinstance(value['gates'], list) and len(value['gates']) == 5,
            'invalid_decision_assessment')
    seen = set()
    for gate in value['gates']:
        closed(gate, {'id', 'name', 'state', 'uncertainty', 'decision_enabled', 'evidence_needed',
                      'role', 'assigned_person', 'budget_approved', 'dependencies',
                      'quantitative_exit', 'unfavorable_result_branch', 'current_evidence'})
        require(gate['id'] in {'DG-1', 'DG-2', 'DG-3', 'DG-4', 'DG-5'} and gate['id'] not in seen,
                'duplicate_or_unknown_decision_gate')
        seen.add(gate['id'])
        require(gate['state'] in {'partial', 'unverified', 'not_met'},
                'unqualified_gate_promotion')
        require(gate['assigned_person'] is None and gate['budget_approved'] is False,
                'assessment_is_not_owner_assignment_or_budget_approval')
        require(all(gate[key] for key in ['uncertainty', 'decision_enabled', 'evidence_needed',
                                         'role', 'quantitative_exit', 'unfavorable_result_branch']),
                'incomplete_decision_gate')
    require(all(dep in seen for gate in value['gates'] for dep in gate['dependencies']),
            'unknown_gate_dependency')
    return {'status': 'assessment_consistent', 'investment_gates': 5,
            'gates_met': 0, 'scope': value['assessment_scope'],
            'meaning': 'Structured uncertainties and exit criteria; no scientific, commercial, rights or funding approval.'}
