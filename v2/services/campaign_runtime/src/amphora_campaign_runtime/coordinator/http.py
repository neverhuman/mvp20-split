"""Scoped graph admission, bounded advancement and paginated observations."""

import asyncio
from amphora_contracts_draft_successor import parse_draft_successor

from amphora_contracts_graph_runtime import (
    CarrySources,
    GraphRunPage,
    GraphRunPageV2,
    GraphRunPageV3,
    SuccessorLineage,
    WaitObservation,
    parse_graph_command,
)
from amphora_contracts_runtime import CommandReceipt
from fastapi import Query, Request
from fastapi.responses import JSONResponse

from ..successors.reads import SuccessorReads
from ..waits.coordinator import WaitCoordinator
from ..waits.reads import WaitReads
from .projections import ProjectionUnavailable
from .reads import GraphReads


def install_graphs(app, admission, advancer, credentials, artifacts=None):
    reads = GraphReads(admission.commands.engine)
    waits = WaitReads(admission.commands.engine)
    successors = SuccessorReads(admission.commands.engine)

    if admission.policies is not None and admission.recipes is not None:
        from ..supervision_preparation.http import install_admission
        install_admission(app, admission, credentials)

    if admission.drafts is not None:
        @app.post("/v1/graph-runs/draft-successors", response_model=CommandReceipt)
        async def admit_draft_successor(request: Request):
            principal = credentials.authenticate(request.headers.get("authorization"))
            command = parse_draft_successor(await request.body())
            return await asyncio.to_thread(admission.admit_draft_successor, principal, command)

        @app.post("/v1/graph-runs/drafts", response_model=CommandReceipt)
        async def admit_draft(request: Request):
            principal = credentials.authenticate(request.headers.get("authorization"))
            command = parse_graph_command("graph.admit_draft", await request.body())
            return await asyncio.to_thread(admission.admit_draft, principal, command)

    @app.post("/v1/graph-runs/successors", response_model=CommandReceipt)
    async def admit_successor(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_graph_command("graph.admit_successor", await request.body())
        return await asyncio.to_thread(admission.admit_successor, principal, command)

    @app.get("/v1/graph-runs/{run_id}/carry-sources", response_model=CarrySources)
    async def carry_sources(run_id: str, request: Request, activation_id: str | None = None):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(successors.sources, principal, run_id, activation_id=activation_id)

    @app.get("/v1/graph-runs/{run_id}/lineage", response_model=SuccessorLineage)
    async def lineage(run_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(successors.lineage, principal, run_id)

    @app.get("/v3/graph-runs/{run_id}", response_model=GraphRunPageV3)
    async def observe_v3(run_id: str, request: Request, after: str | None = None, limit: int = Query(default=100, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reads.run, principal, run_id, after=after, limit=limit, version=3)

    if artifacts is not None:
        receipts = WaitCoordinator(admission.commands.engine, artifacts)

        @app.post("/v1/graph-receipts", response_model=CommandReceipt)
        async def submit_receipt(request: Request):
            principal = credentials.authenticate(request.headers.get("authorization"))
            command = parse_graph_command("graph.submit_receipt", await request.body())
            return await asyncio.to_thread(receipts.submit, principal, command)

    @app.get("/v1/graph-runs/{run_id}/waits/{activation_id}", response_model=WaitObservation)
    async def observe_wait(run_id: str, activation_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(waits.observation, principal, run_id, activation_id)

    @app.get("/v2/graph-runs/{run_id}", response_model=GraphRunPageV2)
    async def observe_v2(run_id: str, request: Request, after: str | None = None, limit: int = Query(default=100, ge=1, le=100)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reads.run, principal, run_id, after=after, limit=limit, version=2)

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
