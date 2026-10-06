"""Explicit operator configuration; secrets are environment-only, no automatic migration."""
import json
import os
from pathlib import Path
from typing import Annotated
from pydantic import Field
from amphora_contracts_core import WireModel
from amphora_contracts_campaigns import ExecutionPlanV4
from amphora_contracts_topology_search import TopologyPolicy
from amphora_tool_protocol import HttpTransport
from ..context.snapshot import _object, _constant
from ..metadata_reads import MetadataTransport
from .peers import TopologyPeers
from .resolution import TopologyResolver, TopologyOperations
from .store import TopologyJournal
from .values import require


class Endpoint(WireModel):
    endpoint: Annotated[str,Field(min_length=1,max_length=512)]
    token_env: Annotated[str,Field(min_length=1,max_length=128,pattern=r'^[A-Za-z_][A-Za-z0-9_]*$')]


class Profile(WireModel):
    policy: TopologyPolicy
    plan: ExecutionPlanV4


class Configuration(WireModel):
    profiles: Annotated[tuple[Profile,...],Field(max_length=64)]
    runtime: Endpoint
    registry: Endpoint


class ConfiguredTopology:
    def __init__(self, configuration, environ):
        self.configuration=configuration
        self._runtime_token=environ[configuration.runtime.token_env]
        self._registry_token=environ[configuration.registry.token_env]
        MetadataTransport('runtime',configuration.runtime.endpoint,self._runtime_token)
        HttpTransport(configuration.registry.endpoint,self._registry_token,timeout=5)
        self.resolver=TopologyResolver(((profile.policy,profile.plan) for profile in configuration.profiles),self.peers)

    @classmethod
    def load(cls, path, environ=None):
        with Path(path).open('rb') as stream:raw=stream.read(8388609)
        require(len(raw)<=8388608,'topology_configuration_size')
        value=json.loads(raw,object_pairs_hook=_object,parse_constant=_constant)
        config=Configuration.model_validate_json(json.dumps(value,allow_nan=False))
        return cls(config,os.environ if environ is None else environ)

    def peers(self, scope):
        return TopologyPeers(scope,self.configuration.runtime.endpoint,self._runtime_token,
                            self.configuration.registry.endpoint,self._registry_token)

    def operations(self, engine):
        return TopologyOperations(TopologyJournal(engine),self.resolver)
