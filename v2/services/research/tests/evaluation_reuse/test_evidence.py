import json

import pytest
from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_core import SchemaRef
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.evaluation_reuse.errors import ReuseError
from amphora_research.evaluation_reuse.evidence import CanonicalEvidence, EvaluationEvidence, ProducedArtifact, read_document, read_exact

from .fixtures import Data, artifact, declaration, producer


def canonical_fixture():
    declared=declaration();data=Data();claim=declared.representation
    raw=b'{"synthetic":"source bytes"}'
    source=artifact(claim.scope,'source',raw,claim.source.schema_ref)
    declared=declared.model_copy(update={'representation':claim.model_copy(update={'source':source})})
    data.contents['source']=raw
    receipt={'wire_version':'1','authority':'synthetic_encoding','scope':claim.scope.model_dump(mode='json'),
        'kind':claim.policy.kind,'semantic_profile':claim.policy.semantic_profile.model_dump(mode='json'),
        'equivalence_profile':claim.policy.equivalence_profile.model_dump(mode='json'),
        'source_sha256':source.sha256,'canonical_sha256':claim.canonical_sha256}
    output=data.add(claim.scope,'canonical',receipt,CanonicalCandidate,'candidate-canonicalization.receipt')
    tool=declared.policy.method.evaluator.model_copy(update={'capability_id':'synthetic.polymer-canonicalize'})
    return declared,data,tool,producer(source,output,tool),receipt


def test_canonical_evidence_binds_exact_byte_reads_and_pins():
    declared,data,tool,proof,_=canonical_fixture()
    result=CanonicalEvidence.resolve(proof,tool,declared,data)
    assert result.receipt.canonical_sha256==declared.representation.canonical_sha256
    assert data.calls==[proof.invocation.inputs[0].artifact,proof.completion.result.outcome.outputs[0].artifact]


@pytest.mark.parametrize('field,value',[('source_sha256','e'*64),('canonical_sha256','e'*64),('kind','sequence')])
def test_shape_valid_canonical_receipt_forgery_is_rejected(field,value):
    declared,data,tool,proof,receipt=canonical_fixture();receipt[field]=value
    output=data.add(declared.context.scope,'forged',receipt,CanonicalCandidate,'candidate-canonicalization.receipt')
    proof=producer(proof.invocation.inputs[0].artifact,output,tool)
    with pytest.raises(ReuseError,match='canonicalization_mismatch'):
        CanonicalEvidence.resolve(proof,tool,declared,data)


def test_tool_input_output_checkpoint_and_scope_binding():
    declared,data,tool,proof,_=canonical_fixture();source=declared.representation.source
    with pytest.raises(ReuseError,match='tool_mismatch'):
        ProducedArtifact.bind(proof,tool.model_copy(update={'release':'9.0.0'}),source)
    with pytest.raises(ReuseError,match='input_mismatch'):
        ProducedArtifact.bind(proof,tool,source.model_copy(update={'artifact_id':'other'}))
    for change in ({'checkpoint':source},{'inputs':()}):
        altered=proof.model_copy(update={'invocation':proof.invocation.model_copy(update=change)})
        with pytest.raises(ReuseError,match='input_mismatch'):ProducedArtifact.bind(altered,tool,source)
    outcome=proof.completion.result.outcome
    for changed in (outcome.model_copy(update={'checkpoint':source}),outcome.model_copy(update={'outputs':outcome.outputs*2})):
        altered=proof.model_copy(update={'completion':proof.completion.model_copy(update={'result':proof.completion.result.model_copy(update={'outcome':changed})})})
        with pytest.raises(ReuseError,match='output_mismatch'):ProducedArtifact.bind(altered,tool,source)
    output=outcome.outputs[0].artifact
    foreign=output.model_copy(update={'scope':output.scope.model_copy(update={'project_id':'other'})})
    with pytest.raises(ReuseError,match='artifact_scope_mismatch'):ProducedArtifact.bind(producer(source,foreign,tool),tool,source)


def evaluation_fixture():
    declared=declaration();data=Data()
    source=data.add(declared.context.scope,'identity',declared.model_dump(mode='json'),EvaluationIdentityInput,'evaluation-identity.input')
    receipt={'wire_version':'1','authority':'synthetic_evaluation','scope':declared.context.scope.model_dump(mode='json'),
        'input_sha256':source.sha256,'canonical_sha256':declared.representation.canonical_sha256,
        'method':declared.policy.method.model_dump(mode='json'),'objective_id':'synthetic-digest-score','unit':'1','value':123}
    output=data.add(declared.context.scope,'evaluation',receipt,SyntheticEvaluationReceipt,'synthetic-evaluation.receipt')
    return declared,data,source,producer(source,output,declared.policy.method.evaluator),receipt


def test_evaluation_binds_original_identity_and_method():
    declared,data,source,proof,_=evaluation_fixture()
    evidence=EvaluationEvidence.resolve(proof,declared.policy,source,data)
    assert evidence.declaration==declared and evidence.receipt.value==123
    assert evidence.production.output==proof.completion.result.outcome.outputs[0].artifact


@pytest.mark.parametrize('field',['input_sha256','canonical_sha256'])
def test_evaluation_receipt_cannot_substitute_another_identity(field):
    declared,data,source,proof,receipt=evaluation_fixture();receipt[field]='e'*64
    output=data.add(declared.context.scope,'forged',receipt,SyntheticEvaluationReceipt,'synthetic-evaluation.receipt')
    with pytest.raises(ReuseError,match='receipt_mismatch'):
        EvaluationEvidence.resolve(producer(source,output,declared.policy.method.evaluator),declared.policy,source,data)


def test_policy_mismatch_never_qualifies_by_matching_result():
    declared,data,source,proof,_=evaluation_fixture()
    policy=declared.policy.model_copy(update={'purpose':'different'})
    with pytest.raises(ReuseError,match='policy_mismatch'):EvaluationEvidence.resolve(proof,policy,source,data)


def test_data_denial_unavailability_schema_bytes_and_document_failures_remain_distinct():
    declared,data,source,proof,_=evaluation_fixture()
    with pytest.raises(ReuseError,match='schema_mismatch'):
        read_document(data,source,CanonicalCandidate,'candidate-canonicalization.receipt')
    with pytest.raises(ReuseError,match='encoding_invalid'):
        read_exact(data,source.model_copy(update={'media_type':'text/plain'}))
    data.contents[source.artifact_id]=b'forged'
    with pytest.raises(ReuseError,match='bytes_mismatch'):read_exact(data,source)
    raw=b'{"x":1,"x":2}'
    bad=artifact(source.scope,'bad',raw,source.schema_ref);data.contents['bad']=raw
    with pytest.raises(ReuseError,match='document_invalid'):read_document(data,bad,EvaluationIdentityInput,'evaluation-identity.input')
    class Unavailable:
        def read(self,_):raise AssessmentPeerUnavailable('peer_deadline')
    with pytest.raises(AssessmentPeerUnavailable,match='peer_deadline'):
        read_document(Unavailable(),source,EvaluationIdentityInput,'evaluation-identity.input')
