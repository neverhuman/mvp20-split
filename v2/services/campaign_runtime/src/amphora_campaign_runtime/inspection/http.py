"""Configured read-only inspection routes; authorization on every request/page."""

import asyncio
from typing import Literal

from amphora_contracts_core import Identifier
from amphora_contracts_runtime import AuditPage, ClaimResponse, CommandReceipt, CompletionRecord, DeliveryPage
from fastapi import Query, Request
from fastapi.responses import JSONResponse

from .cursors import InspectionError


def install_history(app, history, credentials):
    from ..execution_proofs.http import install as install_proofs
    install_proofs(app, history, credentials)
    @app.exception_handler(InspectionError)
    async def error(_request, failure):
        reason = str(failure)
        resnapshot = reason in {"invalid_cursor", "cursor_expired", "cursor_mismatch", "snapshot_unavailable"}
        status = 410 if reason == "cursor_expired" else 409 if resnapshot else 404 if reason.endswith("_unavailable") else 422
        return JSONResponse({"reason_code": reason, "resnapshot": resnapshot}, status_code=status)

    @app.get("/v1/commands/{command_family}/{command_id}", response_model=CommandReceipt | ClaimResponse)
    async def receipt(command_family: Identifier, command_id: Identifier, request: Request,
                      actor_id: Identifier | None = None):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(history.receipt, principal, command_family, command_id, actor_id)

    @app.get("/v1/runs/{run_id}/completions/{completion_id}", response_model=CompletionRecord)
    async def completion(run_id: Identifier, completion_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(history.completion, principal, run_id, completion_id)

    @app.get("/v1/runs/{run_id}/audit", response_model=AuditPage)
    async def audit(run_id: Identifier, request: Request, limit: int = Query(50, ge=1, le=100),
                    cursor: str | None = Query(None, max_length=4096), kind: Identifier | None = None,
                    since_revision: int | None = Query(None, ge=0, le=9007199254740991)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(history.audit, principal, run_id, limit=limit, cursor=cursor,
                                       kind=kind, since_revision=since_revision)

    @app.get("/v1/events/{journal}/{event_id}/deliveries", response_model=DeliveryPage)
    async def deliveries(journal: Literal["run", "policy"], event_id: Identifier, request: Request,
                         limit: int = Query(50, ge=1, le=100), cursor: str | None = Query(None, max_length=4096)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(history.deliveries, principal, journal, event_id, limit=limit, cursor=cursor)

    @app.get("/v1/deliveries/{operation_id}", response_model=DeliveryPage)
    async def delivery(operation_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(history.delivery, principal, operation_id)
