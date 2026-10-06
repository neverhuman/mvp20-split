"""Retained pure proposed/rejected decisions; persistence and owner reads are separate."""
from dataclasses import dataclass
from amphora_contracts_topology_search import TopologyProjection, TopologyRequest
from .edits import apply
from .values import TopologyRejected, digest, encoded, reconstruct, require


@dataclass(frozen=True)
class TopologyProposal:
    canonical: bytes

    @classmethod
    def decide(cls, supplied, request):
        state=supplied.validated()
        request=reconstruct(TopologyRequest,request)
        policy=state.policy()
        require(request.scope==policy.parent.scope and request.policy==state.reference,'topology_request_binding')
        require(request.predecessor.plan_sha256==policy.parent.plan_sha256,'topology_predecessor_binding')
        require(len({carry.target_port for carry in request.carried})==len(request.carried),'topology_duplicate_carry')
        edit=next((item for item in policy.allowed_edits if item.edit_id==request.edit_id),None)
        try:
            require(edit is not None,'topology_edit_not_allowed')
            definition=apply(state,edit,request.successor_revision)
            status,reasons='proposed',[]
        except TopologyRejected as error:
            definition=None;status,reasons='rejected',[str(error)]
        body={'wire_version':'1','authority':'proposal_only','scientific_authority':'not_established',
              'request':request.model_dump(mode='json'),'policy':policy.model_dump(mode='json'),
              'status':status,'reasons':reasons,'definition':None if definition is None else definition.model_dump(mode='json')}
        reference={'scope':request.scope.model_dump(mode='json'),'proposal_id':request.proposal_id,
                   'sha256':digest({'profile':'planning-topology-proposal-v1','document':body})}
        value=TopologyProjection.model_validate_json(encoded(dict(body,reference=reference)))
        return cls(encoded(value.model_dump(mode='json')))

    def to_wire(self):
        value=TopologyProjection.model_validate_json(self.canonical)
        body=value.model_dump(mode='json');reference=body.pop('reference')
        require(reference['scope']==body['request']['scope'] and reference['proposal_id']==body['request']['proposal_id'],'topology_projection_identity')
        require(reference['sha256']==digest({'profile':'planning-topology-proposal-v1','document':body}),'topology_projection_digest')
        return value
