"""Fresh-process reconstruction using only Planning and public contract packages."""

import base64
import json
import sys
from pathlib import Path

from amphora_agent_planning.campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from amphora_agent_planning.campaign_packet import reconstruct
from amphora_agent_planning.campaign_slice_plan import CampaignSlicePlan
from amphora_agent_planning.context import RequestSnapshot
from amphora_contracts_core import Scope


def source(value):
    request = value['request']
    bound = RequestSnapshot.from_bytes(json.dumps(request).encode(), actor_id=request['actor_id'],
        scope=Scope.model_validate(request['reference']['scope']))
    selected = ArtifactContextPlan.bind(bound)
    items = tuple(ArtifactContextItem.available(row, base64.b64decode(value['bodies'][row.reference.artifact_id], validate=True))
                  for row in selected.items)
    return CampaignSlicePlan.from_artifacts(ArtifactContextProjection.bind(selected, items)).with_runtime_unavailable(value['runtime_unavailable'])


def check(path):
    value = json.loads(path.read_bytes())
    packet = reconstruct(source(value), base64.b64decode(value['packet_base64'], validate=True),
        plan_sha256=value['plan_sha256'], packet_sha256=value['packet_sha256'])
    assert packet.fit.document() == value['fit'] and list(packet.included) == value['included']
    return {'packet_sha256': packet.sha256, 'plan_sha256': packet.plan_sha256, 'bytes': len(packet.canonical),
            'input_tokens': packet.fit.measurement.input_tokens, 'output_reserve': packet.fit.document()['output_reserve']}


if __name__ == '__main__':
    print(json.dumps(check(Path(sys.argv[1]))))
