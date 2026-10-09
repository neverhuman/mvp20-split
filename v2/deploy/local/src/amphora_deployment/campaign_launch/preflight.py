"""Public-owner launch checks; Runtime still owns conditional admission and compilation."""
import json
from dataclasses import dataclass
from urllib.parse import quote

from amphora_contracts_core import ArtifactRef
from amphora_contracts_graph_runtime import DraftRevision, DraftValidation
from amphora_contracts_tools import DeploymentSnapshot, ReleaseSnapshot, ToolBinding

from .intent import LaunchError
from .ports import PeerRecordMissing, PreflightRejected


def require_match(condition):
    if not condition:
        raise PreflightRejected()


@dataclass(frozen=True, slots=True)
class InstalledExecutor:
    tool: ToolBinding
    deployment_id: str
    worker_id: str


class LaunchPreflight:
    def __init__(self, policy, runtime, artifacts, registry, deployments, local_check):
        self.policy, self.runtime, self.artifacts, self.registry = policy, runtime, artifacts, registry
        # Operator configuration maps exact tool bindings to installed deployment
        # IDs/worker identities. Neither comes from browser request paths.
        self.deployments, self.local_check = tuple(deployments), local_check

    def check(self, intent):
        try:
            self._check(intent)
        except PeerRecordMissing:
            raise PreflightRejected() from None

    def _check(self, intent):
        self.policy.check(intent)
        payload = json.loads(intent.admission.canonical_bytes)['payload']
        selection = payload['draft']
        scope = intent.request.identity.scope
        draft = self.runtime.read('/v1/definition-drafts/' + quote(selection['draft_id'], safe='')
            + '?revision=' + str(selection['revision']), DraftRevision)
        validation = self.runtime.read('/v1/definition-validations/'
            + quote(selection['validation_id'], safe=''), DraftValidation)
        require_match(draft.scope == validation.scope == scope
            and draft.head.draft_id == validation.draft_id == selection['draft_id']
            and draft.head.revision == validation.revision == selection['revision']
            and draft.head.content_sha256 == validation.content_sha256 == selection['content_sha256']
            and validation.validation_id == selection['validation_id']
            and validation.universe_sha256 == selection['universe_sha256']
            and validation.plan_sha256 == payload['plan_sha256'] and validation.structurally_valid)
        stack, tools = [draft.definition.body], {}
        visited = 0
        while stack:
            body = stack.pop()
            for node in body.nodes:
                visited += 1
                require_match(visited <= 10000)
                if node.kind == 'invoke':
                    require_match(self.policy.permits(node.tool.model_dump(mode='json')))
                    tools[node.tool.model_dump_json()] = node.tool
                if node.kind in {'scatter', 'iterate'}:
                    stack.append(node.body)
        for tool in tools.values():
            matches = [entry for entry in self.deployments if entry.tool == tool]
            require_match(len(matches) == 1)
            expected = matches[0]
            deployment = self.registry.read('/v1/deployments/' + quote(expected.deployment_id, safe=''), DeploymentSnapshot)
            require_match(deployment.scope == scope and deployment.status == 'active'
                and deployment.deployment.deployment_id == expected.deployment_id
                and deployment.deployment.release.tool == tool
                and expected.worker_id in deployment.deployment.workers
                and deployment.deployment.architecture == 'x86_64'
                and deployment.deployment.operating_system == 'linux')
            release = self.registry.read('/v1/releases/' + deployment.deployment.release.descriptor_sha256, ReleaseSnapshot)
            require_match(release.scope == scope and release.status == 'active'
                and release.lock == deployment.deployment.release)
        # Read every retained constant, including nested graph constants and
        # collection inputs. Public ArtifactRef equality checks exact hash/scope.
        values = [draft.definition.model_dump(mode='json'), payload['inputs']]
        references = {}
        while values:
            value = values.pop()
            if type(value) is list:
                values.extend(value)
            elif type(value) is dict:
                if value.get('kind') == 'artifact' and 'artifact' in value:
                    try:
                        reference = ArtifactRef.model_validate_json(json.dumps(value['artifact']))
                    except ValueError:
                        raise LaunchError('launch_artifact_binding_invalid') from None
                    require_match(reference.scope == scope)
                    references[reference.model_dump_json()] = reference
                values.extend(value.values())
        for reference in references.values():
            observed = self.artifacts.read('/v1/artifacts/' + quote(reference.artifact_id, safe=''), ArtifactRef)
            require_match(observed == reference)
        self.local_check(intent, tuple(tools.values()))
