"""Hand-authored public Knowledge records and scripted publication receipts."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from importlib.resources import files
from types import SimpleNamespace

from amphora_agent_planning.access import Principal
from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import ExtractionSnapshot, TraceProjection
from amphora_agent_planning.proposals.context import KnowledgeContext, proposal_schema
from amphora_agent_planning.proposals.inputs import ProposalInputs
from amphora_agent_planning.providers import observe
from amphora_agent_planning.publication import PublicationAttempt, PublicationIdentity, TraceArtifact
from amphora_agent_planning.publication.journal import PublicationState
from amphora_agent_planning.publication.records import PayloadRecord
from amphora_agent_planning.publication.review_record import ReviewRecord
from amphora_agent_planning.source_access import SourceReviewer
from amphora_contracts_core import ArtifactRef
from amphora_contracts_knowledge import DomainGraphSnapshot, GraphAuthoringProfile
from amphora_contracts_planning import extraction_draft_schema, extraction_edit_schema

from ..providers.test_task_output import Response
from ..publication.test_values import receipts
from ..source_access.test_review import inputs


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


class Case:
    def __init__(self, *, history=False, scope=None):
        task, self.data = inputs(scope=scope)
        self.request = task.request.document().model_dump(mode='json')
        self.task = task.document().model_dump(mode='json')
        self.draft = copy.deepcopy(self.data.draft)
        self.task.update(schema_version='2', existing_assertions=[])
        self.draft.update(schema_version='2', edits=[])
        self.scope = task.document().scope
        self.graph = self.task['target']['graph']
        context = self.request['context']
        context['output_schema'] = extraction_edit_schema().model_dump(mode='json')
        prompt = files('amphora_agent_planning.extraction').joinpath('prompts/domain-decomposition-v2.txt').read_bytes()
        context['prompt'].update(sha256=hashlib.sha256(prompt).hexdigest(), size_bytes=len(prompt))
        self.data.artifacts['prompt'] = ArtifactRef.model_validate_json(encode(context['prompt']))
        self.data.payloads['prompt'] = prompt
        applicability = b'explicit synthetic applicability'
        self.context = dict(context['objective'], artifact_id='applicability', sha256=hashlib.sha256(applicability).hexdigest(),
                            size_bytes=len(applicability))
        self.data.artifacts['applicability'] = ArtifactRef.model_validate_json(encode(self.context))
        self.data.payloads['applicability'] = applicability
        context['entries'].append({'artifact': self.context, 'role': 'constraint', 'required': True})
        self.task['target']['applicability'] = self.context
        self.draft['entities'][0].update(label='new-a', context=self.context)
        second = copy.deepcopy(self.draft['entities'][0])
        second.update(local_id='b', label='new-b')
        self.draft['entities'].append(second)
        self.attribution = copy.deepcopy(second['attribution'])
        self.draft['assertions'] = [self.assertion('claim', 'a', 'b')]
        vocabulary = {'wire_version': '1', 'vocabulary_id': 'fixture', 'version': '1', 'entity_types': ['fixture'],
                      'predicates': [{'predicate_id': 'correlates_with', 'description': 'Synthetic association',
                                      'subject_types': ['fixture'], 'object_types': ['fixture']}]}
        vocabulary_ref = {'vocabulary_id': 'fixture', 'version': '1', 'sha256': digest(vocabulary)}
        policy = {'policy_id': 'fixture-policy', 'version': '1', 'sha256': 'a' * 64}
        self.profile = {'wire_version': '1', 'graph': self.graph, 'vocabulary': vocabulary,
                        'vocabulary_reference': vocabulary_ref, 'policy': policy,
                        'origin': 'stored' if history else 'configured_default'}
        self.task['target'].update(vocabulary=vocabulary_ref, policy=policy,
                                  operation_schema=proposal_schema().model_dump(mode='json'))
        self.content = None
        self.known_entities, self.known_assertions = [], []
        if history:
            self.known_entities = [{'graph': self.graph, 'entity_id': 'old-' + key, 'revision': 1} for key in ('a', 'b', 'c')]
            self.known_assertions = [{'graph': self.graph, 'assertion_id': 'old-' + key, 'revision': 1} for key in ('claim', 'retraction')]
            entities = [{'reference': ref, 'entity_type': 'fixture', 'label': label, 'context': self.context, 'supersedes': None}
                        for ref, label in zip(self.known_entities, ('A', 'B', 'C'), strict=True)]
            grounding = {'spans': [self.attribution['quotations'][0]['span']],
                         'conversion_traces': self.task['sources'][0]['conversion_traces'], 'interpretation_artifacts': []}
            assertions = [{'reference': ref, 'subject': self.known_entities[0], 'predicate': 'correlates_with',
                           'object': self.known_entities[1], 'statement': 'Old attributed association',
                           'polarity': 'affirmed', 'posture': 'reported', 'applicability': self.context,
                           'grounding': grounding, 'research_links': [], 'supersedes': None} for ref in self.known_assertions]
            self.content = {'graph': self.graph, 'revision': 1, 'vocabulary': vocabulary_ref, 'policy': policy,
                            'entities': entities, 'assertions': assertions, 'aliases': [], 'retractions': []}
            self.task['existing_entities'] = copy.deepcopy(self.known_entities)
            self.task['existing_assertions'] = copy.deepcopy(self.known_assertions)

    def assertion(self, key, subject, object):
        return {'local_id': key, 'subject': subject, 'predicate': 'correlates_with', 'object': object,
                'statement': 'Synthetic reported association', 'polarity': 'negated', 'posture': 'reported',
                'applicability': self.context, 'attribution': copy.deepcopy(self.attribution)}

    def edit(self, operation, **fields):
        return {'local_id': 'edit-' + str(len(self.draft['edits'])), 'operation': operation,
                'attribution': copy.deepcopy(self.attribution), **fields}

    def bind(self, *, legacy=False):
        if legacy:
            self.task['schema_version'] = '1'
            self.task.pop('existing_assertions')
            self.draft['schema_version'] = '1'
            self.draft.pop('edits')
            for entity in self.draft['entities']:
                entity.pop('context')
            self.request['context']['output_schema'] = extraction_draft_schema().model_dump(mode='json')
            prompt = files('amphora_agent_planning.extraction').joinpath('prompts/domain-decomposition-v1.txt').read_bytes()
            self.request['context']['prompt'].update(sha256=hashlib.sha256(prompt).hexdigest(), size_bytes=len(prompt))
            self.data.artifacts['prompt'] = ArtifactRef.model_validate_json(encode(self.request['context']['prompt']))
            self.data.payloads['prompt'] = prompt
        snapshot = None
        if self.content is not None:
            reference = {'graph': self.graph, 'revision': self.content['revision'], 'sha256': digest(self.content)}
            snapshot = DomainGraphSnapshot.model_validate_json(encode({'wire_version': '1', 'reference': reference,
                                                                       'content': self.content}))
            self.task['target']['base'] = {'snapshot': reference, 'change': {'graph': self.graph, 'change_id': 'base',
                                            'position': self.content['revision'], 'sha256': 'b' * 64}}
        request = RequestSnapshot.from_bytes(encode(self.request), actor_id='fixture', scope=self.scope)
        self.task['request_sha256'] = request.sha256
        task = ExtractionSnapshot.from_bytes(encode(self.task), request)
        knowledge = KnowledgeContext.bind(task, GraphAuthoringProfile.model_validate_json(encode(self.profile)), snapshot)
        review = SourceReviewer(self.data).review(task)
        observed = observe(AttemptBinding(request, 1), Response(encode(self.draft)))
        assert observed.document().proposal is not None, observed.document().reason_code
        projection = TraceProjection.derive('candidate-trace', task, observed)
        principal = Principal('fixture', self.scope, frozenset({'record_attempts'}))
        identity = PublicationIdentity.bind(principal, 'publication', projection.reference(), 'data-owner')
        artifact = TraceArtifact.reviewed(identity, projection, review)
        attempt = PublicationAttempt.first(identity)
        upload, stream, final, derivation = receipts(identity, artifact, attempt)
        attempt = attempt.begun(identity, artifact, upload).start_stream().streamed(stream).start_finalize()
        attempt = attempt.finalized(identity, artifact, final, derivation)
        publication = PublicationState(identity, PayloadRecord(artifact, ReviewRecord.from_review(review)), attempt, 6,
                                       datetime(2026, 1, 1, tzinfo=timezone.utc), ())
        bound = ProposalInputs.from_publication(task, observed, review, knowledge, publication)
        return SimpleNamespace(inputs=bound, task=task, knowledge=knowledge, review=review, observation=observed,
                               publication=publication)
