"""Retained verification facts; supporting payloads remain owned by Data."""
import base64
from dataclasses import dataclass
import json

from amphora_contracts_core import ArtifactRef
from amphora_contracts_tools import ReleaseSnapshot

from ..campaign_context.records import canonical
from ..capability_acceptance.review import AcceptanceReview
from ..context.policy import require
from ..context.snapshot import _object, _constant


@dataclass(frozen=True)
class VerificationWitness:
    canonical: bytes

    @classmethod
    def capture(cls, original, review):
        # Revalidate the actual processed bytes before recording their references.
        verified = AcceptanceReview.bind(original.capability, original.incoming.request.payload,
            review.release.document(), review.evidence)
        report_body = next(row.body for row in verified.evidence if row.reference == verified.report_reference)
        value = {'profile': 'planning-capability-verification.v1',
            'command_sha256': original.incoming.command.sha256,
            'release': verified.release.document().model_dump(mode='json'),
            'report_base64': base64.b64encode(report_body).decode('ascii'),
            'processed_evidence': [row.reference.model_dump(mode='json') for row in verified.evidence]}
        result = cls(canonical(value))
        result.validate(original)
        return result

    def validate(self, original):
        """For immutable Planning records only; never accepts caller attestations."""
        require(type(self.canonical) is bytes and 0 < len(self.canonical) <= 1048576, 'fulfillment_witness_size')
        value = json.loads(self.canonical.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {'profile', 'command_sha256', 'release',
            'report_base64', 'processed_evidence'} and value['profile'] == 'planning-capability-verification.v1'
            and canonical(value) == self.canonical
            and value['command_sha256'] == original.incoming.command.sha256, 'fulfillment_witness_binding')
        spec = original.incoming.request.payload
        require(type(value['processed_evidence']) is list
            and tuple(ArtifactRef.model_validate(row) for row in value['processed_evidence']) == spec.acceptance_evidence,
            'fulfillment_witness_evidence')
        require(type(value['report_base64']) is str, 'fulfillment_witness_report')
        body = base64.b64decode(value['report_base64'], validate=True)
        require(base64.b64encode(body).decode('ascii') == value['report_base64'], 'fulfillment_witness_report')
        AcceptanceReview.review_report(original.capability, spec,
            ReleaseSnapshot.model_validate_json(canonical(value['release'])), body)
