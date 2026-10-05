"""Repair ancestry retains original identity and narrows authority."""

import hashlib

import pytest
from amphora_campaign_runtime.supervision_journal import RequestFrame, RequestSeries
from amphora_campaign_runtime.supervision_requests import ScopeExport
from amphora_campaign_runtime.supervision_requests.binding import encoded
from amphora_campaign_runtime.supervision_scope import DecisionFootprint
from amphora_contracts_supervision import SupervisionRequest

from .test_frames import frame, raw


def next_frame(previous, root=None, change=None, prepared_by='runtime-supervisor'):
    data = previous.request.model_dump(mode='json')
    data['lineage'] = {'ordinal': data['lineage']['ordinal'] + 1,
        'root_request_sha256': (root or previous).request_sha256,
        'parent_request_sha256': previous.request_sha256}
    data['planning_request']['reference']['engagement_id'] = f"repair-{data['lineage']['ordinal']}"
    if change:
        change(data)
    request = SupervisionRequest.model_validate_json(raw(data))
    scope = DecisionFootprint(request.snapshot.cut, previous.footprint().targets,
                              previous.footprint().observations)
    request = request.model_copy(update={'snapshot': ScopeExport(scope).document(),
        'planning_request_sha256': hashlib.sha256(encoded(request.planning_request)).hexdigest()})
    return RequestFrame.capture(request, scope, prepared_by=prepared_by,
                                planning_actor=request.planning_request.actor_id)


def test_sixteen_members_and_exact_original_hashes():
    first = frame()
    series = RequestSeries((first,))
    for _ in range(15):
        series = series.append(next_frame(series.frames[-1], first))
    assert len(series.frames) == 16
    with pytest.raises(ValueError, match='series_size'):
        RequestSeries((*series.frames, first))
    with pytest.raises(ValueError, match='series_size'):
        RequestSeries(())


@pytest.mark.parametrize('path,value,reason', [
    (('reference', 'decision_id'), 'other', 'decision_mismatch'),
    (('checkpoint_id',), 'other', 'decision_mismatch'),
    (('planning_request', 'actor_id'), 'other', 'planning_actor_mismatch'),
    (('planning_request', 'context', 'objective', 'artifact_id'), 'other', 'context_binding_changed'),
    (('planning_request', 'context', 'limits', 'accounting_unit'), 'other', 'accounting_unit_changed'),
    (('planning_request', 'reference', 'engagement_id'), 'decision-1', 'reused_engagement'),
    (('lineage', 'parent_request_sha256'), 'f' * 64, 'lineage_hash'),
])
def test_changed_origin_rejects(path, value, reason):
    first = frame()
    def change(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        if path == ('lineage', 'parent_request_sha256'):
            data['lineage']['root_request_sha256'] = value
    candidate = next_frame(first, change=change)
    with pytest.raises(ValueError, match=reason):
        RequestSeries((first, candidate))


@pytest.mark.parametrize('field', ['max_input_tokens', 'max_output_tokens', 'max_attempts',
                                  'total_tokens', 'total_accounting_units'])
def test_each_call_ceiling_cannot_widen(field):
    first = frame()
    def change(data):
        data['planning_request']['context']['limits'][field] += 1
    with pytest.raises(ValueError, match='limits_widened'):
        RequestSeries((first, next_frame(first, change=change)))


def test_deadline_actor_context_and_ordinal_cannot_change_silently():
    first = frame()
    with pytest.raises(ValueError, match='preparer_mismatch'):
        RequestSeries((first, next_frame(first, prepared_by='other')))
    with pytest.raises(ValueError, match='deadline_widened'):
        RequestSeries((first, next_frame(first, change=lambda d: d.update(deadline_unix_ms=d['deadline_unix_ms'] + 1))))
    with pytest.raises(ValueError, match='lineage_ordinal'):
        RequestSeries((next_frame(first),))
    with pytest.raises(ValueError, match='required_context_lost'):
        RequestSeries((first, next_frame(first, change=lambda d: d['planning_request']['context'].update(entries=[]))))


def test_monotonic_cut_and_narrowed_limits_allowed():
    first = frame()
    def change(data):
        data['snapshot']['cut']['revision'] += 1
        data['planning_request']['runtime_cut']['revision'] += 1
        data['planning_request']['context']['limits']['total_tokens'] -= 1
        data['deadline_unix_ms'] -= 1
    assert len(RequestSeries((first, next_frame(first, change=change))).frames) == 2
    def older(data):
        data['snapshot']['cut']['revision'] -= 1
        data['planning_request']['runtime_cut']['revision'] -= 1
    with pytest.raises(ValueError, match='older_current_cut'):
        RequestSeries((first, next_frame(first, change=older)))


def test_actions_may_narrow_but_not_expand_again():
    first = frame()
    def narrow(data):
        data['planning_request']['context']['allowed_actions'] = ['abstain']
    second = next_frame(first, change=narrow)
    series = RequestSeries((first, second))
    def widen(data):
        data['planning_request']['context']['allowed_actions'] = ['abstain', 'request_evidence']
    with pytest.raises(ValueError, match='actions_widened'):
        series.append(next_frame(second, first, change=widen))


def test_required_context_cannot_be_downgraded():
    first = frame()
    def change(data):
        for item in data['planning_request']['context']['entries']:
            item['required'] = False
    with pytest.raises(ValueError, match='required_context_lost'):
        RequestSeries((first, next_frame(first, change=change)))


def test_only_original_declaration_constraint_may_be_replaced():
    first = frame()
    data = first.request.model_dump(mode='json')
    artifact = dict(data['planning_request']['context']['policy'])
    artifact.update(artifact_id='original-declaration', sha256=data['planning_request']['decision_scope'])
    data['planning_request']['context']['entries'].append(
        {'artifact': artifact, 'role': 'constraint', 'required': True})
    request = SupervisionRequest.model_validate_json(raw(data))
    request = request.model_copy(update={
        'planning_request_sha256': hashlib.sha256(encoded(request.planning_request)).hexdigest()})
    first = RequestFrame.capture(request, first.footprint(), prepared_by='runtime-supervisor',
                                 planning_actor=request.planning_request.actor_id)
    def replace_declaration(data):
        original_digest = data['planning_request']['decision_scope']
        entries = data['planning_request']['context']['entries']
        declaration = next(item for item in entries if item['role'] == 'constraint'
                           and item['artifact']['sha256'] == original_digest)
        declaration['artifact']['sha256'] = 'e' * 64
        declaration['artifact']['artifact_id'] = 'new-declaration'
        data['planning_request']['decision_scope'] = 'e' * 64
    assert RequestSeries((first, next_frame(first, change=replace_declaration)))


def test_third_member_cannot_replace_root_with_previous_parent():
    first = frame()
    second = next_frame(first)
    with pytest.raises(ValueError, match='lineage_hash'):
        RequestSeries((first, second, next_frame(second)))
