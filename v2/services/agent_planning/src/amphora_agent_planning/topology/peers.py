"""Bounded authenticated read-only Runtime/Registry clients; no implicit retry."""
import json
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import GraphRunPageV3, PredecessorCut
from amphora_tool_protocol import HttpTransport, ProtocolError
from amphora_contracts_tools import LockEntry, ReleaseSnapshot
from ..context.snapshot import _object, _constant
from ..registry_access import ObservedRelease
from ..metadata_reads import MetadataTransport, MetadataWindow
from .values import TopologyRejected, encoded, reconstruct, require


class TopologyPeerUnavailable(RuntimeError):
    pass


class TopologyPeers:
    def __init__(self, scope, runtime_endpoint, runtime_token, registry_endpoint, registry_token):
        self.scope=reconstruct(Scope,scope)
        self.runtime=MetadataTransport("runtime",runtime_endpoint,runtime_token)
        self.registry=HttpTransport(registry_endpoint,registry_token,timeout=5)
        self.calls=0

    def read(self, transport, path, model, limit):
        require(self.calls<3,'topology_peer_read_limit')
        self.calls+=1
        try:
            reply=transport.request('GET',path,limit=limit)
        except ProtocolError as error:
            raise TopologyPeerUnavailable('topology_peer_unavailable') from error
        if reply.status in {401,403}:raise PermissionError('planning_access_denied')
        if reply.status==404:raise TopologyRejected('topology_peer_record_unavailable')
        if reply.status!=200:raise TopologyPeerUnavailable('topology_peer_unavailable')
        try:
            value=json.loads(reply.body,object_pairs_hook=_object,parse_constant=_constant)
            return model.model_validate_json(encoded(value))
        except (ValueError,TypeError,RecursionError,UnicodeError) as error:
            raise TopologyPeerUnavailable('topology_peer_protocol_error') from error

    def parent(self, supplied):
        cut=reconstruct(PredecessorCut,supplied)
        require(self.calls<3,'topology_peer_read_limit')
        self.calls+=1
        try:
            value=self.runtime.read('/v3/graph-runs/'+cut.run_id+'?limit=1',MetadataWindow('runtime',seconds=5))
        except ValueError as error:
            code=str(error)
            if code=='metadata_denied':raise PermissionError('planning_access_denied') from error
            if code=='metadata_missing':raise TopologyRejected('topology_peer_record_unavailable') from error
            reason='topology_peer_protocol_error' if code in {'metadata_protocol','metadata_media'} else 'topology_peer_unavailable'
            raise TopologyPeerUnavailable(reason) from error
        require(value.scope==self.scope and value.run_id==cut.run_id and value.plan_sha256==cut.plan_sha256 and value.revision==cut.revision,
                'topology_current_parent_changed')
        return value

    def release(self, supplied):
        lock=reconstruct(LockEntry,supplied)
        value=self.read(self.registry,'/v1/releases/'+lock.descriptor_sha256,ReleaseSnapshot,262144)
        return ObservedRelease.bind(value,self.scope,lock).document()
