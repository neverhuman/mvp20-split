"""Exact task-to-request binding; no caller-supplied graph head becomes authority."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_planning import (
    ExtractionTask,
    ExtractionTaskV2,
    extraction_draft_schema,
    extraction_edit_schema,
)
from pydantic import ValidationError

from ..context import RequestSnapshot
from ..context.policy import require
from ..context.snapshot import _constant, _object


@dataclass(frozen=True)
class ExtractionSnapshot:
    canonical: bytes
    request: RequestSnapshot

    @classmethod
    def from_bytes(cls, raw, request):
        require(type(raw) is bytes and 0 < len(raw) <= 262144, "extraction_task_size")
        original = request.document()
        request = RequestSnapshot.bind(original, actor_id=original.actor_id, scope=original.reference.scope)
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
            require(type(value) is dict, "invalid_extraction_task")
            model = ExtractionTaskV2 if value.get("schema_version") == "2" else ExtractionTask
            task = model.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_extraction_task") from exc
        require(task.scope == original.reference.scope and task.engagement == original.reference,
                "extraction_request_scope")
        require(task.request_sha256 == request.sha256, "extraction_request_digest")
        require(original.purpose == "knowledge_decomposition", "extraction_request_purpose")
        profile = extraction_edit_schema() if task.schema_version == "2" else extraction_draft_schema()
        require(original.context.output_schema == profile, "extraction_output_profile")
        require(task.target.graph.scope == task.scope, "extraction_graph_scope")
        if task.target.base is not None:
            require(task.target.base.snapshot.graph == task.target.graph and
                    task.target.base.change.graph == task.target.graph, "extraction_head_graph")
        selected = [entry.artifact for entry in original.context.entries]
        sources = [entry.artifact for entry in original.context.entries if entry.role == "source"]
        require(task.target.applicability is None or task.target.applicability in selected,
                "extraction_context_unselected")
        identities = set()
        for item in task.sources:
            source = item.source
            require(source.scope == task.scope and source.raw.scope == task.scope, "extraction_source_scope")
            require(source.raw in sources, "extraction_source_unselected")
            key = (source.source_id, source.revision_id)
            require(key not in identities, "extraction_source_duplicate")
            identities.add(key)
            traces = set()
            for trace in item.conversion_traces:
                require(trace.scope == task.scope, "extraction_trace_scope")
                require(trace.trace_id not in traces, "extraction_trace_duplicate")
                traces.add(trace.trace_id)
        for ref in task.existing_entities:
            require(ref.graph == task.target.graph, "extraction_entity_graph")
        assertions = task.existing_assertions if task.schema_version == "2" else ()
        if task.schema_version == "2":
            require(task.target.base is not None or not (task.existing_entities or assertions),
                    "extraction_selection_without_head")
        for ref in assertions:
            require(ref.graph == task.target.graph, "extraction_assertion_graph")
        for refs in (task.existing_entities, assertions, task.known_questions, task.known_needs):
            require(len({ref.model_dump_json() for ref in refs}) == len(refs), "extraction_reference_duplicate")
        for ref in (*task.known_questions, *task.known_needs):
            require(ref.scope == task.scope, "extraction_research_scope")
        canonical = json.dumps(task.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False, allow_nan=False).encode("utf-8")
        require(len(canonical) <= 262144, "extraction_task_size")
        return cls(canonical, request)

    def document(self):
        model = ExtractionTaskV2 if json.loads(self.canonical).get("schema_version") == "2" else ExtractionTask
        return model.model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()
