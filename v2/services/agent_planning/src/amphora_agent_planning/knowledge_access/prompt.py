"""Bounded graph data and exact schema documents, not a live context-fit claim."""

import hashlib
import json

from amphora_contracts_knowledge import GraphChangeProposal

from ..context.policy import require
from ..proposals.context import KnowledgeContext
from ..providers.profiles import OutputProfiles


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def schema_document(model, reference):
    schema = model.model_json_schema(mode='validation')
    schema.update({'$schema': 'https://json-schema.org/draft/2020-12/schema',
                   '$id': f'urn:amphora:{reference.schema_id}:{reference.version}:validation'})
    require(hashlib.sha256(encode(schema) + b'\n').hexdigest() == reference.sha256, 'graph_prompt_schema_digest')
    return schema


class GraphPrompt:
    @staticmethod
    def render(review, knowledge):
        task = review.task
        require(knowledge.task_sha256 == task.sha256, 'graph_prompt_task_binding')
        knowledge = KnowledgeContext.bind(task, knowledge.profile(), knowledge.snapshot())
        packet = json.loads(review.prompt.render(task, review.bundle))
        facts = knowledge.index()
        selected = list(task.document().existing_entities)
        assertions = []
        for reference in getattr(task.document(), 'existing_assertions', ()):
            require(reference in facts.assertions, 'graph_prompt_assertion_missing')
            assertion = facts.assertions[reference]
            assertions.append(assertion.model_dump(mode='json'))
            for endpoint in (assertion.subject, assertion.object):
                if endpoint not in selected:
                    selected.append(endpoint)
        aliases = []
        for reference in selected:
            require(reference in facts.entities, 'graph_prompt_entity_missing')
            target = facts.aliases.get(reference.entity_id)
            if target is not None:
                aliases.append({'source': reference.model_dump(mode='json'), 'target': target.model_dump(mode='json')})
                if target not in selected:
                    selected.append(target)
        output = task.request.document().context.output_schema
        graph_data = {
            'profile': knowledge.profile().model_dump(mode='json'),
            'snapshot': None if knowledge.snapshot_bytes is None else knowledge.snapshot().reference.model_dump(mode='json'),
            'context_sha256': hashlib.sha256(knowledge.profile_bytes + b'\n' + (knowledge.snapshot_bytes or b'')).hexdigest(),
            'entities': [facts.entities[ref].model_dump(mode='json') for ref in selected],
            'assertions': assertions,
            'aliases': aliases,
            'retracted_assertions': [ref.model_dump(mode='json') for ref in sorted(facts.retracted,
                key=lambda ref: (ref.assertion_id, ref.revision)) if ref in getattr(task.document(), 'existing_assertions', ())],
            'selection': 'explicit_task_records_and_endpoint_alias_dependencies',
            'output_schema': schema_document(OutputProfiles.draft_model(output), output),
            'operation_schema': schema_document(GraphChangeProposal, task.document().target.operation_schema),
        }
        require(len(encode(graph_data)) <= 1048576, 'graph_prompt_context_limit')
        packet.update(profile='planning-grounded-extraction-input.v1', graph_data=graph_data)
        raw = encode(packet)
        require(len(raw) <= 8388608, 'graph_prompt_packet_limit')
        return raw
