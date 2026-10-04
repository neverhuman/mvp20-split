"""Installed Planning reads actual Research; public DTOs only, no peer implementation."""

import importlib.util
import json
import os
import sys
from pathlib import Path

from amphora_agent_planning.campaign_context import ResearchSelection
from amphora_agent_planning.campaign_research_access import (
    CampaignResearchTransport,
    ResearchRecordReader,
)
from amphora_agent_planning.context import RequestSnapshot
from amphora_agent_planning.research_view_access import (
    ResearchViewReader,
    ResearchViewTransport,
    ResearchViewWindow,
    ViewSelection,
)
from amphora_contracts_core import Scope
from amphora_contracts_research_views import (
    ObservationSeriesRequest,
    PropertyViewRequest,
    SpecimenViewRequest,
)


def run(path):
    assert all(importlib.util.find_spec(name) is None for name in (
        "amphora_research", "amphora_knowledge", "amphora_data_artifacts", "amphora_campaign_runtime", "fastapi"))
    value = json.loads(path.read_bytes())
    scope = Scope.model_validate_json(json.dumps(value["request"]["reference"]["scope"]))
    request = RequestSnapshot.from_bytes(json.dumps(value["request"]).encode(), actor_id="fixture", scope=scope)
    selection = ResearchSelection.from_bytes(json.dumps(value["selection"]).encode(), request)
    endpoint, token = os.environ["CAMPAIGN_RESEARCH_ENDPOINT"], os.environ["CAMPAIGN_RESEARCH_TOKEN"]
    records = ResearchRecordReader(CampaignResearchTransport(endpoint, token)).review(selection)
    reader = ResearchViewReader(ResearchViewTransport(endpoint, token))
    window = ResearchViewWindow()
    pages = {}
    for name, model in (("specimens", SpecimenViewRequest), ("properties", PropertyViewRequest),
                        ("observation_series", ObservationSeriesRequest)):
        selected = ViewSelection.bind(model.model_validate_json(json.dumps(value["queries"][name])), request)
        result = reader.read(selected, window)
        pages[name] = {"failure": result.failure, "page": None if result.page is None else result.page.document().model_dump(mode="json"),
            "sha256": None if result.page is None else result.page.sha256, "calls": result.calls}
        # Continuation is explicitly requested here by the acceptance consumer.
        if result.page is not None and result.page.document().next_position is not None:
            following = ViewSelection.bind(selected.document().model_copy(update={"position": result.page.document().next_position}), request)
            next_result = reader.read(following, window)
            assert next_result.failure is None
            pages[name]["next"] = next_result.page.document().model_dump(mode="json")
    catalog = None
    if pages["specimens"]["failure"] is None:
        selected = ViewSelection.bind(SpecimenViewRequest.model_validate_json(json.dumps(value["queries"]["specimens"])), request)
        catalog = reader.catalog(selected, window).model_dump(mode="json")
    return {"pid": os.getpid(), "context": json.loads(records.context.canonical),
        "record_hashes": [record.sha256 for record in records.context.records],
        "record_failures": [failure.code for failure in records.failures], "record_calls": records.calls,
        "pages": pages, "catalog": catalog, "view_calls": window.calls}


if __name__ == "__main__":
    try:
        print(json.dumps(run(Path(sys.argv[1]))))
    except Exception as error:  # noqa: BLE001 - keep process boundary failures free of credentials
        raise SystemExit("Campaign Research probe failed: " + type(error).__name__) from None
