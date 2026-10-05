"""Bounded authored addresses, not a replacement for Runtime compilation."""

from dataclasses import dataclass

from amphora_contracts_planning import CampaignNodeAddress, FutureCampaignDraft

from ..context.policy import require


@dataclass(frozen=True)
class AuthoredNode:
    address: CampaignNodeAddress
    node: object


@dataclass(frozen=True)
class AuthoredCampaign:
    candidate: FutureCampaignDraft
    nodes: tuple[AuthoredNode, ...]

    @classmethod
    def bind(cls, candidate):
        candidate = FutureCampaignDraft.model_validate_json(candidate.model_dump_json(warnings=False))
        pending = [((), candidate.definition.body)]
        nodes, scopes = [], 0
        while pending:
            path, scope = pending.pop()
            scopes += 1
            # Match documented Runtime structural ceilings without interpreting edges/types.
            require(len(path) <= 16 and scopes <= 1024, 'campaign_authored_scope_limit')
            identifiers = [node.node_id for node in scope.nodes]
            require(len(set(identifiers)) == len(identifiers), 'campaign_authored_duplicate_node')
            for node in scope.nodes:
                address = CampaignNodeAddress(scope_path=path, node_id=node.node_id)
                nodes.append(AuthoredNode(address, node))
                require(len(nodes) <= 4096, 'campaign_authored_node_limit')
                if node.kind in {'scatter', 'iterate'}:
                    pending.append(((*path, node.node_id), node.body))
        return cls(candidate, tuple(nodes))

    def resolve(self, address):
        require(self.bind(self.candidate) == self, 'campaign_authored_binding')
        address = CampaignNodeAddress.model_validate_json(address.model_dump_json(warnings=False))
        found = next((node for node in self.nodes if node.address == address), None)
        require(found is not None, 'campaign_producer_unknown')
        return found
