import copy
import json

import pytest
from amphora_agent_planning.campaign_research_access import (
    CampaignResearchTransport,
    CampaignResearchWindow,
)
from amphora_agent_planning.peer_reads.profile import ReadProfile
from amphora_agent_planning.peer_reads.transport import BoundedReadTransport
from amphora_contracts_research import (
    EvidenceAssessmentRequest,
    EvidenceAssessmentStatus,
)

from ..campaign_context.test_records import values, wire
from ..knowledge_access.test_transport import peer  # noqa: F401


@pytest.mark.parametrize("kind,path", [("question", "/v1/questions/read"), ("need", "/v1/evidence-needs/read"),
                                       ("assessment", "/v1/assessments/read")])
def test_each_compiled_route_uses_exact_body_and_authenticated_bounded_http(peer, kind, path):  # noqa: F811
    server, _, _ = peer
    record = wire(kind, values()[kind])
    reference = record.request if kind == "assessment" else record.reference
    server.body = record.model_dump_json().encode()
    transport = CampaignResearchTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32)
    window = CampaignResearchWindow()
    assert transport.read(path, reference, window) == record
    assert server.calls == [(path, "Bearer " + "t" * 32, reference.model_dump(mode="json"))]
    with pytest.raises(ValueError, match="research_peer_path"):
        transport.read("/v1/assessments", reference, window)
    assert window.calls == 1 and window.consumed == len(server.body)


def test_large_exact_assessment_requests_do_not_widen_legacy_request_cap(peer):  # noqa: F811
    server, _, _ = peer
    status = values()["assessment"]
    reference = status["request"]
    base = reference["receipts"][0]
    reference["receipts"] = [{**copy.deepcopy(base), "artifact_id": f"selected-receipt-{i}"} for i in range(16)]
    status["outcome"]["assessment"]["request"] = copy.deepcopy(reference)
    request = EvidenceAssessmentRequest.model_validate_json(json.dumps(reference))
    assert 4096 < len(request.model_dump_json().encode()) < 262144
    server.body = json.dumps(status).encode()
    endpoint = f"http://127.0.0.1:{server.server_port}"
    transport = CampaignResearchTransport(endpoint, "t" * 32)
    assert transport.read("/v1/assessments/read", request, CampaignResearchWindow()).request == request
    legacy = ReadProfile("research", 15, 64, 4194304, {
        "/v1/assessments/read": (EvidenceAssessmentRequest, EvidenceAssessmentStatus, 1048576)})
    from amphora_agent_planning.peer_reads.profile import ReadWindow

    with pytest.raises(ValueError, match="research_request_size"):
        BoundedReadTransport(endpoint, "t" * 32, legacy).read("/v1/assessments/read", request, ReadWindow(legacy, 15))
    assert len(server.calls) == 1 and legacy.request_bytes == 4096


def test_new_profile_bounds_are_explicit_and_do_not_mutate_routes():
    window = CampaignResearchWindow()
    for _ in range(160):
        window.start()
    with pytest.raises(ValueError, match="research_read_call_limit"):
        window.start()
    with pytest.raises(TypeError):
        window.profile.routes["/v1/assessments"] = window.profile.routes["/v1/assessments/read"]
    for count, size in ((161, 4096), (160, 262145), (160, True), (True, 4096)):
        with pytest.raises(ValueError, match="peer_read_limits"):
            ReadProfile("research", 20, count, 4194304, dict(window.profile.routes), request_bytes=size)
    with pytest.raises(ValueError, match="research_read_deadline"):
        CampaignResearchWindow(seconds=21)
