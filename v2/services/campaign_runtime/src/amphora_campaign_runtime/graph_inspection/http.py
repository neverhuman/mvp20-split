"""Configured authenticated graph snapshot/detail/invalidation reads."""

import asyncio

from amphora_contracts_core import Digest, Identifier
from amphora_contracts_graph_runtime import (
    GraphInvalidationPage,
    GraphNodeDetail,
    GraphReadQuery,
    GraphSnapshotPage,
    GraphValuePage,
)
from fastapi import Query, Request

from .details import GraphDetails
from .inputs import InputObservationError, NodeInputs
from amphora_contracts_node_inputs import NodeInputObservation
from fastapi.responses import JSONResponse
from .events import GraphInvalidations
from .snapshots import GraphSnapshots


def install_graph_inspection(app, history, credentials):
    from ..graph_navigation.http import install_graph_navigation

    install_graph_navigation(app, history, credentials)
    @app.middleware("http")
    async def input_cache_policy(request, call_next):
        response = await call_next(request)
        parts = request.url.path.strip("/").split("/")
        if len(parts) == 6 and parts[:2] == ["v1", "graph-observations"] and parts[3] == "nodes" and parts[5] == "inputs":
            response.headers["Cache-Control"] = "no-store"
        return response

    inputs = NodeInputs(history.engine)

    @app.exception_handler(InputObservationError)
    async def input_integrity_error(_request, _error):
        return JSONResponse(status_code=503, content={"reason_code": "input_observation_integrity_unavailable"},
                            headers={"Cache-Control": "no-store"})

    @app.get("/v1/graph-observations/{run_id}/nodes/{activation_id}/inputs", response_model=NodeInputObservation)
    async def node_inputs(run_id: Identifier, activation_id: Digest, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        observation = await asyncio.to_thread(inputs.read, principal, run_id, activation_id)
        return JSONResponse(content=observation.model_dump(mode="json"), headers={"Cache-Control": "no-store"})

    snapshots = GraphSnapshots(history.engine, history.cursors)
    details = GraphDetails(history.engine, history.cursors)
    invalidations = GraphInvalidations(history.engine, history.cursors)

    @app.get("/v1/graph-observations/{run_id}/nodes", response_model=GraphSnapshotPage)
    async def nodes(run_id: Identifier, request: Request, scope_key: Digest | None = None, frontier_only: bool = False,
                    cursor: str | None = Query(None, max_length=4096), limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(snapshots.page, principal, run_id,
            query=GraphReadQuery(scope_key=scope_key, frontier_only=frontier_only), cursor=cursor, limit=limit)

    @app.get("/v1/graph-observations/{run_id}/nodes/{activation_id}", response_model=GraphNodeDetail)
    async def node(run_id: Identifier, activation_id: Digest, request: Request,
                   snapshot_token: str = Query(min_length=1, max_length=4096),
                   cursor: str | None = Query(None, max_length=4096), limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(details.node, principal, run_id, activation_id,
                                       snapshot_token=snapshot_token, cursor=cursor, limit=limit)

    @app.get("/v1/graph-observations/{run_id}/nodes/{activation_id}/outputs/{port}", response_model=GraphValuePage)
    async def values(run_id: Identifier, activation_id: Digest, port: Identifier, request: Request,
                     snapshot_token: str = Query(min_length=1, max_length=4096),
                     cursor: str | None = Query(None, max_length=4096), limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(details.values, principal, run_id, activation_id, port,
                                       snapshot_token=snapshot_token, cursor=cursor, limit=limit)

    @app.get("/v1/graph-observations/{run_id}/invalidations", response_model=GraphInvalidationPage)
    async def events(run_id: Identifier, request: Request, cursor: str = Query(min_length=1, max_length=4096),
                     limit: int = Query(50, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(invalidations.page, principal, run_id, cursor=cursor, limit=limit)
