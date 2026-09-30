"""Explicit bounded navigation routes; unknown filters are rejected rather than ignored."""

import asyncio

from amphora_contracts_core import Digest, Identifier
from amphora_contracts_graph_runtime import (
    GraphScopePage,
    GraphTopologyPage,
    GraphTopologyQuery,
)
from fastapi import Query, Request

from ..graph_inspection.policy import require
from .reads import GraphNavigation


def install_graph_navigation(app, history, credentials):
    navigation = GraphNavigation(history.engine, history.cursors)

    @app.get("/v1/graph-observations/{run_id}/scopes", response_model=GraphScopePage)
    async def scopes(run_id: Identifier, request: Request, snapshot_token: str = Query(min_length=1, max_length=4096),
                     parent_activation_id: Digest | None = None, cursor: str | None = Query(None, max_length=4096),
                     limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        require(set(request.query_params) <= {"snapshot_token", "parent_activation_id", "cursor", "limit"}, "invalid_page_request")
        return await asyncio.to_thread(navigation.scopes, principal, run_id, snapshot_token=snapshot_token,
                                       parent_activation_id=parent_activation_id, cursor=cursor, limit=limit)

    @app.get("/v1/graph-observations/{run_id}/scopes/{scope_key}/topology", response_model=GraphTopologyPage)
    async def topology(run_id: Identifier, scope_key: Digest, request: Request,
                       snapshot_token: str = Query(min_length=1, max_length=4096), focus_activation_id: Digest | None = None,
                       radius: int = Query(1, ge=0, le=2), cursor: str | None = Query(None, max_length=4096),
                       limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        require(set(request.query_params) <= {"snapshot_token", "focus_activation_id", "radius", "cursor", "limit"}, "invalid_page_request")
        return await asyncio.to_thread(navigation.topology, principal, run_id, scope_key, snapshot_token=snapshot_token,
            query=GraphTopologyQuery(focus_activation_id=focus_activation_id, radius=radius), cursor=cursor, limit=limit)
