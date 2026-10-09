"""Publish sourced demo context through public Data and Knowledge protocols."""
import copy
import hashlib
from pathlib import Path
from local_numeric_configuration import write
from verify_local_owner_records import Scenario


class ScientificKnowledge(Scenario):
    def create(self, fixture, schema):
        raw = (Path(__file__).parent / 'knowledge_source.txt').read_bytes()
        artifact = self.publish(raw, schema, 'text/plain')
        rights = {'wire_version': '1', 'reference': {'scope': self.scope, 'rights_id': 'authored-demo', 'revision': 1},
            'supersedes': None, 'status': 'granted', 'allowed_uses': ['read', 'process'],
            'expires_at': None, 'retention': 'retain_audit_payload'}
        self.call('artifact', '/v1/acquisition/rights', rights)
        source = {'wire_version': '1', 'reference': {'scope': self.scope, 'source_id': 'polymer-demo-context',
            'revision_id': 'r1', 'raw': artifact}, 'delivery': {'issuer_id': 'internal-demo', 'delivery_id': 'first'},
            'method': {'connector_id': 'authored-synthetic', 'connector_version': '1',
                'configuration_sha256': hashlib.sha256(b'{}').hexdigest(), 'format': 'utf8_document'},
            'rights': rights['reference'], 'supersedes': None, 'completeness': 'complete'}
        prepared = self.call('artifact', '/v1/acquisition/prepare', source)
        converted = self.publish(prepared['content_json_utf8'].encode(), prepared['schema_ref'])
        trace = self.call('artifact', '/v1/acquisition/retain', {'wire_version': '1', 'source': source,
            'trace_id': 'polymer-demo-conversion', 'output': converted})
        graph = {'scope': self.scope, 'graph_id': 'polymer-screening-context'}
        profile = self.call('knowledge', '/v1/graph-profiles/read', graph)
        grounding = {'spans': [{'source': source['reference'], 'unit': 'byte', 'start': 0,
            'end': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}],
            'conversion_traces': [trace], 'interpretation_artifacts': []}
        labels = {'screening': 'Illustrative polymer evaluation plan', 'hansen': 'Hansen solvency screen',
            'hansen-inputs': 'Supplied Hansen parameters and radius', 'arrhenius': 'Arrhenius viscosity adjustment',
            'viscosity-inputs': 'Supplied viscosity, activation energy and temperatures',
            'missing-evidence': 'Missing synthesis and laboratory confirmation'}
        def reference(entity):
            return {'graph': graph, 'entity_id': entity, 'revision': 1}
        operations = [{'operation': 'add_entity', 'entity': {'reference': reference(key),
            'entity_type': 'concept', 'label': label, 'context': artifact, 'supersedes': None}}
            for key, label in labels.items()]
        relations = [('hansen', 'requires', 'hansen-inputs', 'The demo Hansen calculation requires supplied parameters; measured compatibility is not established.'),
            ('arrhenius', 'requires', 'viscosity-inputs', 'The demo viscosity calculation requires supplied reference values and temperatures; process suitability is not established.'),
            ('hansen', 'part_of', 'screening', 'Hansen screening is one method in the illustrative evaluation plan.'),
            ('arrhenius', 'part_of', 'screening', 'Viscosity adjustment is another method in the illustrative evaluation plan.'),
            ('screening', 'requires', 'missing-evidence', 'Synthesis and laboratory evidence remain missing before any experimental-readiness claim.')]
        for index, (subject, predicate, target, statement) in enumerate(relations):
            claim = copy.deepcopy(fixture['proposal']['operations'][2]['assertion'])
            claim.update(reference={'graph': graph, 'assertion_id': 'context-' + str(index + 1), 'revision': 1},
                subject=reference(subject), object=reference(target), predicate=predicate, statement=statement,
                posture='hypothesis', applicability=artifact, grounding=grounding, research_links=[], supersedes=None)
            operations.append({'operation': 'add_assertion', 'assertion': claim})
        proposal = {'wire_version': '1', 'graph': graph, 'change_id': 'authored-context-r1', 'base': None,
            'vocabulary': profile['vocabulary_reference'], 'policy': profile['policy'],
            'description': 'Record explicitly synthetic polymer screening planning context.',
            'rationale': 'Manual engineering decomposition; no scientific or LLM extraction authority.',
            'grounding': grounding, 'operations': operations}
        write(self.output / 'proposal.json', proposal)
        accepted = self.call('knowledge', '/v1/graph-proposals', proposal)
        write(self.output / 'decision.json', accepted)
        assert accepted['decision']['outcome'] == 'accepted', 'Knowledge context rejected'
        revision = accepted['decision']['head']['snapshot']
        snapshot = self.call('knowledge', '/v1/graph-snapshots/read', revision)
        assert len(snapshot['content']['entities']) == 6 and len(snapshot['content']['assertions']) == 5
        association = {'role': 'planning_context', 'revision': revision, 'methods': [
            {'method_id': 'solvency', 'entity_ids': ['hansen', 'hansen-inputs']},
            {'method_id': 'viscosity', 'entity_ids': ['arrhenius', 'viscosity-inputs']}]}
        result = {'scope': self.scope, 'knowledge': association, 'artifact': artifact, 'source': source,
            'rights': rights, 'converted': converted, 'trace': trace, 'accepted': accepted, 'snapshot': snapshot}
        write(self.output / 'records.json', result)
        return result
