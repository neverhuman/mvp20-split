"""Exact public evidence binding; returned evidence is not a reuse decision."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_candidate_canonicalization import CanonicalCandidate
from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_evaluation_identity import EvaluationIdentityInput
from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_synthetic_evaluation import SyntheticEvaluationReceipt

from ..assessment.reader import AssessmentPeerUnavailable, _decode
from ..candidate_registration.profiles import schema_reference
from .errors import ReuseError, require


def published_schema(model, name):
    document = model.model_json_schema(mode='validation')
    document.update({'$schema':'https://json-schema.org/draft/2020-12/schema',
                     '$id':f'urn:amphora:{name}:1:validation'})
    raw = (json.dumps(document,sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
    return SchemaRef(schema_id=name,version='1',sha256=hashlib.sha256(raw).hexdigest())


def read_exact(reader, source):
    require(source.size_bytes <= 262144 and source.media_type == 'application/json', 'reuse_source_encoding_invalid')
    raw = reader.read(source)
    require(type(raw) is bytes and len(raw) == source.size_bytes
            and hashlib.sha256(raw).hexdigest() == source.sha256, 'reuse_source_bytes_mismatch')
    return raw


def read_document(reader, source, model, name):
    require(source.schema_ref == published_schema(model, name), 'reuse_source_schema_mismatch')
    raw = read_exact(reader, source)
    try:
        return _decode(model, raw)
    except AssessmentPeerUnavailable as error:
        raise ReuseError('reuse_source_document_invalid') from error


@dataclass(frozen=True, slots=True)
class ProducedArtifact:
    proof: AcceptedToolExecution
    source: ArtifactRef
    output: ArtifactRef

    @classmethod
    def bind(cls, proof, tool, expected_input):
        proof = AcceptedToolExecution.model_validate_json(proof.model_dump_json())
        invocation, completion = proof.invocation, proof.completion
        result = completion.result.outcome
        require(completion.canonical_result and result.status == 'succeeded'
            and invocation.activation_id == completion.activation_id
            and invocation.invocation_id == completion.result.invocation_id, 'reuse_producer_not_canonical_success')
        require(invocation.tool == tool, 'reuse_producer_tool_mismatch')
        require(len(invocation.inputs) == 1 and invocation.inputs[0].port == 'parameters'
            and invocation.inputs[0].artifact == expected_input and invocation.checkpoint is None,
            'reuse_producer_input_mismatch')
        require(len(result.outputs) == 1 and result.outputs[0].port == 'result' and result.checkpoint is None,
            'reuse_producer_output_mismatch')
        output = result.outputs[0].artifact
        require(expected_input.scope == output.scope == completion.scope, 'reuse_producer_artifact_scope_mismatch')
        return cls(proof, expected_input, output)


@dataclass(frozen=True, slots=True)
class CanonicalEvidence:
    production: ProducedArtifact
    receipt: CanonicalCandidate

    @classmethod
    def resolve(cls, proof, tool, declared, reader):
        claim = declared.representation
        production = ProducedArtifact.bind(proof, tool, claim.source)
        require(claim.source.schema_ref == schema_reference('candidate-space.' + claim.policy.kind),
            'reuse_direct_representation_required')
        read_exact(reader, production.source)
        receipt = read_document(reader, production.output, CanonicalCandidate, 'candidate-canonicalization.receipt')
        require(receipt.scope == claim.scope == declared.context.scope == claim.source.scope
            and receipt.kind == claim.policy.kind and receipt.semantic_profile == claim.policy.semantic_profile
            and receipt.equivalence_profile == claim.policy.equivalence_profile
            and receipt.source_sha256 == claim.source.sha256 and receipt.canonical_sha256 == claim.canonical_sha256,
            'reuse_canonicalization_mismatch')
        return cls(production, receipt)


@dataclass(frozen=True, slots=True)
class EvaluationEvidence:
    production: ProducedArtifact
    declaration: EvaluationIdentityInput
    receipt: SyntheticEvaluationReceipt

    @classmethod
    def resolve(cls, proof, evaluation_policy, identity_source, reader):
        production = ProducedArtifact.bind(proof, evaluation_policy.method.evaluator, identity_source)
        declaration = read_document(reader, identity_source, EvaluationIdentityInput, 'evaluation-identity.input')
        receipt = read_document(reader, production.output, SyntheticEvaluationReceipt, 'synthetic-evaluation.receipt')
        require(declaration.policy == evaluation_policy, 'reuse_evaluation_policy_mismatch')
        require(receipt.scope == declaration.context.scope == identity_source.scope
            and receipt.input_sha256 == identity_source.sha256
            and receipt.canonical_sha256 == declaration.representation.canonical_sha256
            and receipt.method == evaluation_policy.method, 'reuse_evaluation_receipt_mismatch')
        return cls(production, declaration, receipt)
