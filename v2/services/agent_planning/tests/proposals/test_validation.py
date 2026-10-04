"""Independent operation/findings oracles; no Knowledge acceptance is asserted."""

import copy

import pytest
from amphora_agent_planning.proposals.validator import GraphCandidateValidator

from .support import Case


def validate(case):
    return GraphCandidateValidator().validate(case.bind().inputs)


def test_additions_preserve_negation_unknown_confidence_and_exact_interpretation_grounding():
    case = Case()
    case.draft['assertions'][0]['attribution']['confidence'] = 'unknown'
    result = validate(case)
    proposal = result.proposal()
    assert result.outcome == 'proposed' and result.validation == 'quotation_and_structure_only'
    assert [operation.operation for operation in proposal.operations] == ['add_entity', 'add_entity', 'add_assertion']
    assertion = proposal.operations[-1].assertion
    assert assertion.polarity == 'negated' and assertion.posture == 'reported'
    assert assertion.grounding.spans[0] == proposal.grounding.spans[0]
    assert assertion.grounding.interpretation_artifacts == proposal.grounding.interpretation_artifacts
    assert proposal.grounding.interpretation_artifacts[0].artifact_id == 'output'
    assert not any(finding.code == 'low_confidence' for finding in result.findings)
    assert validate(case).proposal_bytes == result.proposal_bytes


def test_missing_context_withholds_only_affected_entity_and_dependent_assertion():
    case = Case()
    case.draft['entities'][0]['context'] = None
    result = validate(case)
    assert result.outcome == 'partial'
    assert [operation.entity.label for operation in result.proposal().operations] == ['new-b']
    assert {(finding.location, finding.code) for finding in result.findings} >= {
        ('/entities/0', 'required_context_missing'), ('/assertions/0', 'assertion_endpoint_unresolved')}


def test_wrong_quote_never_becomes_accepted_grounding_but_independent_candidate_survives():
    case = Case()
    case.draft['entities'][0]['attribution']['quotations'][0]['text'] = 'invented quotation'
    result = validate(case)
    assert result.outcome == 'partial' and len(result.proposal().operations) == 1
    assert any(finding.code == 'quotation_bytes' for finding in result.findings)


@pytest.mark.parametrize('case_name,code', [('duplicate-id', 'duplicate_candidate_identity'),
                                         ('same-label', 'ambiguous_candidate_label')])
def test_duplicate_candidates_are_not_silently_coalesced(case_name, code):
    case = Case()
    field = 'local_id' if case_name == 'duplicate-id' else 'label'
    case.draft['entities'][1][field] = case.draft['entities'][0][field]
    result = validate(case)
    assert result.proposal() is None and any(finding.code == code for finding in result.findings)


def test_case_sensitive_scientific_labels_are_distinct():
    case = Case()
    case.draft['entities'][0]['label'] = 'Co'
    case.draft['entities'][1]['label'] = 'CO'
    assert len(validate(case).proposal().operations) == 3


def test_inferred_reported_claim_is_withheld_without_blocking_explicit_hypothesis():
    case = Case()
    case.draft['assertions'][0]['attribution']['origin'] = 'inferred'
    result = validate(case)
    assert len(result.proposal().operations) == 2
    assert any(finding.code == 'inferred_claim_requires_hypothesis' for finding in result.findings)
    case.draft['assertions'][0]['posture'] = 'hypothesis'
    assert validate(case).proposal().operations[-1].assertion.posture == 'hypothesis'


def test_correction_and_retraction_use_exact_targets_and_do_not_add_replacement():
    case = Case(history=True)
    case.draft['edits'] = [case.edit('correct_assertion', prior=case.known_assertions[0], replacement_local_id='claim')]
    case.draft['edits'].append(case.edit('retract_assertion', assertion=case.known_assertions[1]))
    result = validate(case)
    operations = result.proposal().operations
    assert [operation.operation for operation in operations] == ['add_entity', 'add_entity', 'correct_assertion', 'retract_assertion']
    replacement = operations[2].replacement
    assert replacement.reference.assertion_id == 'old-claim' and replacement.reference.revision == 2
    assert replacement.supersedes == operations[2].prior
    assert replacement.grounding.interpretation_artifacts


def test_unknown_prior_never_turns_replacement_into_an_addition():
    case = Case(history=True)
    prior = dict(case.known_assertions[0], assertion_id='unknown')
    case.draft['edits'] = [case.edit('correct_assertion', prior=prior, replacement_local_id='claim')]
    result = validate(case)
    assert [operation.operation for operation in result.proposal().operations] == ['add_entity', 'add_entity']
    assert any(finding.code == 'assertion_prior_not_selected' for finding in result.findings)


def test_conflicting_edits_are_withheld_without_falling_back_to_implicit_add():
    case = Case(history=True)
    case.draft['edits'] = [case.edit('correct_assertion', prior=case.known_assertions[0], replacement_local_id='claim')]
    case.draft['edits'].append(case.edit('retract_assertion', assertion=case.known_assertions[0]))
    result = validate(case)
    assert all(operation.operation == 'add_entity' for operation in result.proposal().operations)
    assert any(finding.code == 'conflicting_edit_targets' for finding in result.findings)


def test_context_revision_requires_same_label_and_type_then_rebinds_dependent_endpoint():
    case = Case(history=True)
    case.draft['entities'][0]['label'] = 'A'
    case.draft['edits'] = [case.edit('revise_entity_context', prior=case.known_entities[0], replacement_local_id='a')]
    proposal = validate(case).proposal()
    assert [operation.operation for operation in proposal.operations] == ['add_entity', 'revise_entity_context', 'add_assertion']
    assert proposal.operations[-1].assertion.subject == proposal.operations[1].replacement.reference
    case.draft['entities'][0]['label'] = 'renamed'
    result = validate(case)
    assert len(result.proposal().operations) == 1
    assert any(finding.code == 'context_edit_changes_identity' for finding in result.findings)


def test_merge_retains_exact_selected_same_type_references():
    case = Case(history=True)
    case.draft['edits'] = [case.edit('merge_entities', source=case.known_entities[0], target=case.known_entities[1])]
    operation = validate(case).proposal().operations[-1]
    assert operation.operation == 'merge_entities' and operation.source.entity_id == 'old-a'
    assert operation.target.entity_id == 'old-b'


def test_ambiguous_existing_labels_require_resolution_even_when_model_picks_one():
    case = Case(history=True)
    case.content['entities'][1]['label'] = 'A'
    case.draft['entities'][0].update(label='A', matches=[case.known_entities[0]])
    result = validate(case)
    assert any(finding.code == 'ambiguous_entity_label' for finding in result.findings)
    assert len(result.proposal().operations) == 1


def test_contradictions_and_model_diagnostics_remain_visible_without_global_quality_veto():
    case = Case()
    alternative = copy.deepcopy(case.draft['assertions'][0])
    alternative.update(local_id='opposite', polarity='affirmed')
    case.draft['assertions'].append(alternative)
    case.draft['diagnostics'] = [{'code': 'conflict', 'target_path': '/assertions', 'kind': 'contradiction',
                                  'description': 'Synthetic incompatible claims'}]
    result = validate(case)
    assert result.outcome == 'proposed' and not result.withheld
    assert [operation.assertion.polarity for operation in result.proposal().operations[2:]] == ['negated', 'affirmed']
    assert any(finding.code == 'model_reported_contradiction' for finding in result.findings)
