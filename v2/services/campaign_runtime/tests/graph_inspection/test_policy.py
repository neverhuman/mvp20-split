"""Independent rejection oracles for incomplete event windows and page bounds."""

import pytest
from amphora_campaign_runtime.graph_inspection.events import InvalidationWindow
from amphora_campaign_runtime.graph_inspection.policy import page_limit
from amphora_campaign_runtime.inspection.cursors import InspectionError


@pytest.mark.parametrize("previous,current,revisions", [
    (3, 2, []), (0, 3, [1, 3]), (0, 3, [1, 1]), (0, 3, [2, 1]),
    (0, 3, [1, 2]), (0, 0, [1]),
])
def test_incomplete_or_reordered_history_requires_resnapshot(previous, current, revisions):
    rows = tuple({"revision": revision, "event_id": f"event-{index}"} for index, revision in enumerate(revisions))
    with pytest.raises(InspectionError, match="snapshot_unavailable"):
        InvalidationWindow(previous, current, rows, 100).verified()


@pytest.mark.parametrize("limit", [0, 101, -1, True, "1", 1.0])
def test_domain_page_boundary_rejects_invalid_limits(limit):
    with pytest.raises(InspectionError, match="invalid_page_request"):
        page_limit(limit)
