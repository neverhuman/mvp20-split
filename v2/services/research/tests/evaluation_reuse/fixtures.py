import hashlib
import json
from pathlib import Path

from amphora_contracts_core import ArtifactRef
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_research.evaluation_reuse.evidence import published_schema


def declaration():
    return EvaluationIdentityInput.model_validate_json((Path(__file__).parent / 'input.json').read_bytes())


def artifact(scope, name, raw, schema):
    return ArtifactRef(scope=scope, artifact_id=name, sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw), media_type='application/json', schema_ref=schema)


def producer(source, output, tool):
    return AcceptedToolExecution.model_validate_json(json.dumps({'wire_version':'1','authority':'accepted_execution',
        'worker_id':'worker', 'invocation': {'node_id':'node','activation_id':'activation','invocation_id':'invocation',
            'tool':tool.model_dump(mode='json'),'inputs':[{'port':'parameters','artifact':source.model_dump(mode='json')}],
            'timeout_seconds':60},
        'completion':{'scope':source.scope.model_dump(mode='json'),'run_id':'run','completion_id':'completion',
            'activation_id':'activation','accepted_run_revision':3,'canonical_result':True,
            'retention_reservation_ids':['reservation'],
            'result':{'schema_version':'1','invocation_id':'invocation','attempt_id':'attempt','fence':1,
                'outcome':{'status':'succeeded','outputs':[{'port':'result','artifact':output.model_dump(mode='json')}]}}}}))


class Data:
    def __init__(self):
        self.contents = {}
        self.calls = []

    def add(self, scope, name, record, model, schema_name):
        raw = json.dumps(record).encode()
        reference = artifact(scope,name,raw,published_schema(model,schema_name))
        self.contents[reference.artifact_id] = raw
        return reference

    def read(self, reference):
        self.calls.append(reference)
        return self.contents[reference.artifact_id]
