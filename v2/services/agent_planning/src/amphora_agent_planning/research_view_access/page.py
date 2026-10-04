"""Exact query/page binding; content observations are not scientific acceptance."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_research_views import ResearchViewCatalog, research_view_schema

from ..context.policy import require
from .query import VIEWS, ViewSelection, canonical, scoped


@dataclass(frozen=True)
class ViewPage:
    selection: ViewSelection
    canonical: bytes

    @classmethod
    def bind(cls, selection, response):
        selection = ViewSelection.bind(selection.document(), selection.request)
        model = VIEWS[selection.view][1]
        require(type(response) is model, "research_view_response_type")
        response = model.model_validate(response.model_dump(mode="python", warnings=False))
        raw = response.model_dump_json(warnings=False).encode("utf-8")
        require(len(raw) <= 1048576, "research_view_response_size")
        page = model.model_validate_json(raw)
        query = selection.document()
        require(page.request == query and page.query_sha256 == selection.query_sha256, "research_view_identity")
        scoped(page, selection.request.document().reference.scope)
        start = 0 if query.position is None else query.position.offset
        require(start <= page.total, "research_view_window")
        end = min(start + query.limit, page.total)
        items = page.points if selection.view == "observation_series" else page.rows
        require(len(items) == end - start, "research_view_window")
        expected = None if end == page.total else {"query_sha256": selection.query_sha256, "offset": end}
        actual = None if page.next_position is None else page.next_position.model_dump(mode="json")
        require(actual == expected, "research_view_continuation")
        if selection.view == "properties":
            require(page.total == len(query.observations) and
                    tuple(row.reference for row in page.rows) == query.observations[start:end], "research_view_observations")
        elif selection.view == "specimens":
            identities = [row.sample.reference for row in page.rows]
            require(len(set(identities)) == len(identities), "research_view_duplicate_sample")
            for row in page.rows:
                require(row.material is None or (row.material.reference == row.sample.material_state and
                        row.material.candidate == row.sample.candidate), "research_view_material")
        encoded = canonical(page.model_dump(mode="json"))
        require(len(encoded) <= 1048576, "research_view_response_size")
        return cls(selection, encoded)

    def document(self):
        return VIEWS[self.selection.view][1].model_validate_json(self.canonical)

    @property
    def sha256(self):
        return hashlib.sha256(self.canonical).hexdigest()


def catalog(response, experiment):
    require(type(response) is ResearchViewCatalog, "research_view_response_type")
    response = ResearchViewCatalog.model_validate(response.model_dump(mode="python", warnings=False))
    raw = response.model_dump_json(warnings=False).encode("utf-8")
    require(len(raw) <= 1048576, "research_view_response_size")
    result = ResearchViewCatalog.model_validate_json(raw)
    require(result.experiment == experiment, "research_view_identity")
    require({entry.view_id for entry in result.views} == set(VIEWS), "research_view_catalog")
    require(all(entry.result_schema == research_view_schema(entry.view_id) for entry in result.views),
            "research_view_schema")
    return result
