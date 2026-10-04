"""Native task/prompt/output/quotation/trace checks for reviewed fixture responses."""

import json
from importlib.resources import files
from pathlib import Path

from amphora_agent_planning.context import AttemptBinding, RequestSnapshot
from amphora_agent_planning.extraction import (
    ExtractionSnapshot,
    PromptTemplate,
    SourceBundle,
    SourceText,
    TraceProjection,
)
from amphora_agent_planning.providers import observe
from amphora_agent_planning.providers.capture import unknown_usage
from amphora_agent_planning.providers.port import ProviderReply
from amphora_agent_planning.providers.profiles import OutputProfiles
from amphora_contracts_core import Scope
from amphora_contracts_planning import ExtractionDraftV2, extraction_edit_schema

from .semantic_review import canonical, digest


def inputs(case):
    value = json.loads((Path(__file__).parent / "fixtures/extraction.json").read_bytes())
    scope = {"tenant_id": "semantic-fixture", "project_id": case.case_id}

    def replace(item):
        if isinstance(item, dict):
            if set(item) == {"tenant_id", "project_id"}:
                item.update(scope)
            if item.get("artifact_id") == "source-utf8":
                item.update(sha256=digest(case.source), size_bytes=len(case.source))
            for child in item.values():
                replace(child)
        elif isinstance(item, list):
            for child in item:
                replace(child)
    replace(value)
    prompt = files("amphora_agent_planning.extraction").joinpath("prompts/domain-decomposition-v2.txt").read_bytes()
    value["request"]["context"]["prompt"].update(sha256=digest(prompt), size_bytes=len(prompt))
    value["request"]["context"]["output_schema"] = extraction_edit_schema().model_dump(mode="json")
    request = RequestSnapshot.from_bytes(canonical(value["request"]), actor_id="fixture", scope=Scope.model_validate(scope))
    value["task"].update(schema_version="2", existing_assertions=[], request_sha256=request.sha256)
    task = ExtractionSnapshot.from_bytes(canonical(value["task"]), request)
    bundle = SourceBundle.bind(task, (SourceText.bind(task.document().sources[0], case.source),))
    packet = PromptTemplate.bind(request.document().context.prompt, prompt).render(task, bundle)
    return task, bundle, packet


def inspect(response):
    task, bundle, packet = inputs(response.case)
    class Provider:
        def supports(self, model):
            return True

        def reply(self, binding):
            return ProviderReply((response.output,), unknown_usage())
    observed = observe(AttemptBinding(task.request, 1), Provider())
    trace = TraceProjection.derive(response.response_id, task, observed).document()
    assert trace.authority == "interpretation_only" and trace.validation == "profile_only"
    quote_status, quote_count = "not_proposed", 0
    if observed.document().proposal is not None:
        draft = ExtractionDraftV2.model_validate_json(observed.document().proposal.payload_json)
        try:
            for _, item in OutputProfiles.attributed_items(draft):
                quote_count += len(item.attribution.quotations)
                bundle.verify_attribution(item.attribution)
        except ValueError:
            quote_status = "invalid"
        else:
            quote_status = "verified_geometry_only" if quote_count else "no_quoted_candidates"
    return {"status": observed.document().status, "quotation": quote_status, "quotation_count": quote_count,
        "trace": trace.model_dump(mode="json"),
        "packet": json.loads(packet)}
