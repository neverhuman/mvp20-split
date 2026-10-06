"""Fresh owner reads precede publication; retained observations remain reconstructable."""
from amphora_contracts_topology_search import TopologyRequest
from .document import TopologyDocument, parent_matches
from .edits import local_scope
from .policy import TopologyPolicyState
from .proposal import TopologyProposal
from .values import TopologyRejected, reconstruct, require


class TopologyResolver:
    def __init__(self, profiles, peer_factory):
        profiles=tuple(profiles)
        require(len(profiles)<=64,'topology_profile_limit')
        self.profiles=tuple(TopologyPolicyState.bind(policy,plan,()) for policy,plan in profiles)
        keys=[(s.policy().parent.scope,s.reference) for s in self.profiles]
        require(len(set(keys))==len(keys),'topology_duplicate_profile')
        self.peer_factory=peer_factory

    def resolve(self, principal, supplied):
        request=reconstruct(TopologyRequest,supplied)
        principal.require('propose_topology',request.scope)
        state=next((s for s in self.profiles if s.reference==request.policy and s.policy().parent.scope==request.scope),None)
        require(state is not None,'topology_profile_unavailable')
        require(state.policy().parent.plan_sha256==request.predecessor.plan_sha256,'topology_predecessor_binding')
        peer=self.peer_factory(request.scope)
        observation=peer.parent(request.predecessor)
        parent_matches(observation,request)
        edit=next((e for e in state.policy().allowed_edits if e.edit_id==request.edit_id),None)
        locks=[]
        if edit is not None:
            if edit.kind=='evaluator_swap':
                old=next((lock for lock in state.plan().document.lock.tools if lock.tool==edit.expected_tool),None)
                new=edit.replacement
            else:
                old=None;new=edit.transform
                try:
                    _,target=local_scope(state.plan().document.definition.model_dump(mode='json'),edit.target)
                    old=next((lock for lock in state.plan().document.lock.tools if lock.tool.model_dump(mode='json')==target['tool']),None)
                except TopologyRejected:
                    pass  # Named invalid target is retained by pure proposal policy.
            locks=list(dict.fromkeys(lock for lock in (old,new) if lock is not None))
        observed=tuple(peer.release(lock) for lock in locks)
        qualified=TopologyPolicyState.bind(state.policy(),state.plan(),observed)
        proposal=TopologyProposal.decide(qualified,request)
        return TopologyDocument.create(principal.actor_id,qualified,observation,proposal)


class TopologyOperations:
    def __init__(self, journal, resolver):
        self.journal,self.resolver=journal,resolver

    def propose(self, principal, request):
        record=self.resolver.resolve(principal,request)
        return self.journal.register(principal,record).projection

    def read(self, principal, proposal_id):
        value=self.journal.read(principal,proposal_id)
        return None if value is None else value.projection
