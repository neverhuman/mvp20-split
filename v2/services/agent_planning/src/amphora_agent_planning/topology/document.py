"""Reconstructable immutable owner evidence; no current-rights grant on historical read."""
import json
from dataclasses import dataclass
from pydantic import TypeAdapter
from amphora_contracts_core import Identifier
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_graph_runtime import GraphRunPageV3
from amphora_contracts_tools import ReleaseSnapshot
from amphora_contracts_topology_search import TopologyPolicy, TopologyProjection
from ..context.snapshot import _object, _constant
from .policy import TopologyPolicyState
from .proposal import TopologyProposal
from .values import digest, encoded, reconstruct, require


def parent_matches(observation, request):
    require(observation.scope==request.scope and observation.run_id==request.predecessor.run_id and
            observation.plan_sha256==request.predecessor.plan_sha256 and observation.revision==request.predecessor.revision,
            'topology_current_parent_changed')


@dataclass(frozen=True)
class TopologyDocument:
    canonical: bytes

    @classmethod
    def create(cls, actor_id, state, parent, proposal):
        TypeAdapter(Identifier).validate_python(actor_id,strict=True)
        state=state.validated()
        parent=reconstruct(GraphRunPageV3,parent)
        projection=proposal.to_wire()
        require(TopologyProposal.decide(state,projection.request)==proposal,'topology_projection_reconstruction')
        parent_matches(parent,projection.request)
        body={'format':'planning-topology-record-v1','actor_id':actor_id,'policy':state.policy().model_dump(mode='json'),
            'plan':state.plan().model_dump(mode='json'),'releases':[r.model_dump(mode='json') for r in state.releases()],
            'parent_observation':parent.model_dump(mode='json'),'projection':projection.model_dump(mode='json')}
        raw=encoded(body)
        require(len(raw)<=8388608,'topology_record_size')
        return cls(raw)

    @classmethod
    def load(cls, raw):
        require(type(raw) is bytes and 0<len(raw)<=8388608,'topology_record_size')
        value=json.loads(raw,object_pairs_hook=_object,parse_constant=_constant)
        require(type(value) is dict and set(value)=={'format','actor_id','policy','plan','releases','parent_observation','projection'} and
                value['format']=='planning-topology-record-v1','topology_record_shape')
        state=TopologyPolicyState.bind(TopologyPolicy.model_validate_json(encoded(value['policy'])),
            ExecutionPlanV4.model_validate_json(encoded(value['plan'])),
            tuple(ReleaseSnapshot.model_validate_json(encoded(r)) for r in value['releases']))
        result=cls.create(value['actor_id'],state,GraphRunPageV3.model_validate_json(encoded(value['parent_observation'])),
                          TopologyProposal(encoded(value['projection'])))
        require(result.canonical==raw,'topology_record_canonical')
        return result

    @property
    def projection(self):
        return TopologyProjection.model_validate_json(encoded(json.loads(self.canonical)['projection']))

    @property
    def actor_id(self):
        return json.loads(self.canonical)['actor_id']

    @property
    def sha256(self):
        return digest(json.loads(self.canonical))
