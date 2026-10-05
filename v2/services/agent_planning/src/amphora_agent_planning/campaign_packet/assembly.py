"""Required-first complete-envelope fitting; no dispatch, accounting or journal."""

import base64
import hashlib
from dataclasses import dataclass

from ..campaign_artifact_context import (
    ArtifactContextItem,
    ArtifactContextPlan,
    ArtifactContextProjection,
)
from ..campaign_packet_profiles import CampaignInstructions, PacketBudget
from ..campaign_packet_profiles.budget import PacketFit
from ..campaign_slice_plan.slices import ordered
from ..context.policy import require
from .render import render


@dataclass(frozen=True)
class PreparedCampaignPacket:
    canonical: bytes
    fit: PacketFit
    plan_sha256: str
    included: tuple[int, ...]

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()


@dataclass(frozen=True)
class PacketPreparation:
    packet: PreparedCampaignPacket | None
    failure: str | None
    missing_required: tuple[str, ...] = ()


def original_artifacts(plan):
    """Recheck original roots/roles/bytes before trusting the instruction source."""
    expected = ArtifactContextPlan.bind(plan.request)
    rows = [row for row in plan.slices if row.lane == 'artifact']
    require(len(rows) == len(expected.items), 'campaign_packet_artifact_coverage')
    items = []
    for row, planned in zip(rows, expected.items, strict=True):
        value = row.document()
        payload = value['payload']
        require(value['identity'] == planned.reference.model_dump(mode='json') and row.required == planned.required and
                all(payload[key] == item for key, item in planned.document().items()), 'campaign_packet_artifact_binding')
        body = payload['body_base64']
        if body is None:
            item = ArtifactContextItem.unavailable(planned, payload['reason'])
        else:
            item = ArtifactContextItem.available(planned, base64.b64decode(body, validate=True))
        require(item.payload() == payload, 'campaign_packet_artifact_payload')
        require(value['observations'] == [{'kind': 'artifact', 'identity': value['identity'],
                'sha256': item.observation_sha256}], 'campaign_packet_artifact_observation')
        items.append(item)
    return ArtifactContextProjection.bind(expected, tuple(items))


def prepare(plan):
    require(ordered(plan.slices) == plan.slices, 'campaign_packet_slice_order')
    budget = PacketBudget.bind(plan.request)
    artifacts = original_artifacts(plan)
    missing = tuple(item.planned.reference.artifact_id for item in artifacts.missing_required)
    require(missing == plan.missing_required, 'campaign_packet_required_binding')
    if missing:
        return PacketPreparation(None, 'required_artifact_unavailable', missing)
    prompt = next(item for item in artifacts.items if 'prompt' in item.planned.roles)
    instructions = CampaignInstructions.bind(plan.request, prompt.planned.reference, prompt.body)
    included = tuple(index for index, row in enumerate(plan.slices) if row.required)
    raw = render(plan, instructions, included)
    if len(raw) > 8388608:
        return PacketPreparation(None, 'required_packet_size')
    fit = budget.inspect(raw)
    if not fit.fits:
        return PacketPreparation(None, 'required_input_limit')
    for index, row in enumerate(plan.slices):
        if row.required:
            continue
        trial = (*included, index)
        candidate = render(plan, instructions, trial)
        if len(candidate) > 8388608:
            continue
        measured = budget.inspect(candidate)
        if measured.fits:
            included, raw, fit = trial, candidate, measured
    return PacketPreparation(PreparedCampaignPacket(raw, fit, plan.sha256, included), None)
