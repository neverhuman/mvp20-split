"""Explicitly configured synthetic admission routes; no general graph activation."""

import asyncio

from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_runtime import ClaimResponse, CommandReceipt, parse_command
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

from ..persistence.commands import CommandConflict
from .authority import AuthorityCommands
from .claims import RuntimeLeases
from .model import TransitionError


def install_admission(app, admission, credentials):
    leases = RuntimeLeases(admission.commands.engine)
    authority = AuthorityCommands(admission.commands.engine)
    @app.exception_handler(TransitionError)
    async def denied(_request, error):
        return JSONResponse({"reason_code": str(error)}, status_code=401 if str(error) == "unauthenticated" else 403)

    @app.exception_handler(CommandEncodingError)
    async def malformed(_request, _error):
        return JSONResponse({"reason_code": "invalid_command"}, status_code=422)

    @app.exception_handler(CommandConflict)
    async def conflict(_request, _error):
        return JSONResponse({"reason_code": "command_identity_conflict"}, status_code=409)

    @app.exception_handler(DBAPIError)
    async def unavailable(_request, _error):
        return JSONResponse({"reason_code": "persistence_unavailable"}, status_code=503)

    @app.post("/v1/fixture-runs", response_model=CommandReceipt)
    async def admit(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_command("runtime.admit_fixture", await request.body())
        return await asyncio.to_thread(admission.admit, principal, command)


    @app.post("/v1/invocations/claim", response_model=ClaimResponse | CommandReceipt)
    async def claim(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_command("runtime.claim", await request.body())
        return await asyncio.to_thread(leases.claim, principal, command)

    @app.post("/v1/attempts/renew", response_model=CommandReceipt)
    async def renew(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_command("runtime.renew", await request.body())
        return await asyncio.to_thread(leases.renew, principal, command)


    @app.post("/v1/runs/cancel", response_model=CommandReceipt)
    async def cancel(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_command("runtime.cancel", await request.body())
        return await asyncio.to_thread(authority.cancel, principal, command)

    @app.post("/v1/workers/revoke", response_model=CommandReceipt)
    async def revoke(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_command("runtime.revoke_worker", await request.body())
        return await asyncio.to_thread(authority.revoke, principal, command)
