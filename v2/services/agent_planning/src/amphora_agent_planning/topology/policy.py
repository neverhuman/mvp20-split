"""Exact original parent and configured edit universe, without owner authentication."""
from dataclasses import dataclass
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_core import SchemaRef
from amphora_contracts_topology_search import TopologyPolicy
from ..registry_access import ObservedRelease
from .values import digest, encoded, reconstruct, require


@dataclass(frozen=True)
class TopologyPolicyState:
    policy_bytes: bytes
    plan_bytes: bytes
    release_bytes: tuple[bytes, ...]

    @classmethod
    def bind(cls, policy, plan, releases):
        policy=reconstruct(TopologyPolicy,policy)
        plan=reconstruct(ExecutionPlanV4,plan)
        require(plan.sha256==digest(plan.document.model_dump(mode='json')),'topology_parent_digest')
        definition=plan.document.definition
        actual=digest({'profile':'amphora-executable-definition-v4','definition':definition.model_dump(mode='json')})
        require(actual==plan.document.lock.definition_sha256==policy.parent.definition_sha256,'topology_definition_digest')
        require(plan.sha256==policy.parent.plan_sha256 and definition.scope==policy.parent.scope,'topology_parent_binding')
        require(definition.context==plan.document.lock.context,'topology_parent_context')
        require(len({edit.edit_id for edit in policy.allowed_edits})==len(policy.allowed_edits),'topology_duplicate_edit')
        releases=tuple(releases)
        require(len(releases)<=320,'topology_release_limit')
        observed=tuple(ObservedRelease.bind(record,policy.parent.scope) for record in releases)
        keys=[record.document().lock.tool for record in observed]
        require(len(set(keys))==len(keys),'topology_duplicate_release')
        # Validate bounded local structure; full control/type compilation remains Runtime-owned.
        pending=[((),definition.body)];nodes=scopes=0
        while pending:
            path,body=pending.pop();nodes+=len(body.nodes);scopes+=1
            require(len(path)<=16 and nodes<=4096 and scopes<=1024,'topology_graph_bound')
            require(len({node.node_id for node in body.nodes})==len(body.nodes),'topology_duplicate_node')
            pending.extend(((*path,node.node_id),node.body) for node in body.nodes if node.kind in {'iterate','scatter'})
        return cls(encoded(policy.model_dump(mode='json')),encoded(plan.model_dump(mode='json')),tuple(r.canonical for r in observed))

    def policy(self):
        return TopologyPolicy.model_validate_json(self.policy_bytes)

    def plan(self):
        return ExecutionPlanV4.model_validate_json(self.plan_bytes)

    def releases(self):
        return tuple(ObservedRelease(value).document() for value in self.release_bytes)

    def validated(self):
        return self.bind(self.policy(),self.plan(),self.releases())

    @property
    def reference(self):
        return SchemaRef(schema_id='planning.topology-policy',version='1',sha256=digest({'profile':'planning-topology-policy-v1','policy':self.policy().model_dump(mode='json')}))

    def release(self, lock, *, active=True):
        found=next((record for record in self.releases() if record.lock.tool==lock.tool),None)
        require(found is not None and found.lock==lock,'topology_release_lock')
        require(not active or found.status=='active','topology_release_inactive')
        require(found.descriptor.tool.side_effects=='pure' and found.descriptor.authority_ceiling=='synthetic_only','topology_release_authority')
        return found.descriptor
