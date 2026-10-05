"""Historical byte reconstruction is not fresh processing or dispatch permission."""

import hashlib

from ..context.policy import require
from .assembly import prepare


def reconstruct(plan, raw, *, plan_sha256, packet_sha256):
    require(type(raw) is bytes and 0 < len(raw) <= 8388608, 'campaign_packet_replay_size')
    require(plan.sha256 == plan_sha256, 'campaign_packet_replay_plan')
    require(hashlib.sha256(raw).hexdigest() == packet_sha256, 'campaign_packet_replay_digest')
    outcome = prepare(plan)
    require(outcome.packet is not None, 'campaign_packet_replay_unavailable')
    require(outcome.packet.canonical == raw, 'campaign_packet_replay_bytes')
    return outcome.packet
