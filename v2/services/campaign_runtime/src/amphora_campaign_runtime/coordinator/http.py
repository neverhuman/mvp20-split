"""Scoped graph admission, bounded advancement and paginated observations."""

import asyncio

from amphora_contracts_graph_runtime import GraphRunPage, parse_graph_command
from amphora_contracts_runtime import CommandReceipt
from fastapi import Query, Request
from fastapi.responses import JSONResponse

from .projections import ProjectionUnavailable
from .reads import GraphReads


def install_graphs(app, admission, advancer, credentials):
    reads = GraphReads(admission.commands.engine)

    @app.exception_handler(ProjectionUnavailable)
    async def projection_unavailable(_request, _error):
        return JSONResponse({"reason_code": "artifact_projection_unavailable"}, status_code=503)

    @app.post("/v1/graph-runs", response_model=CommandReceipt)
    async def admit(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_graph_command("graph.admit", await request.body())
        return await asyncio.to_thread(admission.admit, principal, command)

    @app.post("/v1/graph-runs/advance", response_model=CommandReceipt)
    async def advance(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_graph_command("graph.advance", await request.body())
        return await asyncio.to_thread(advancer.advance, principal, command)

    @app.get("/v1/graph-runs/{run_id}", response_model=GraphRunPage)
    async def observe(run_id: str, request: Request, after: str | None = None, limit: int = Query(default=100, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reads.run, principal, run_id, after=after, limit=limit)
