"""Explicitly configured synthetic admission routes; no general graph activation."""

import asyncio

from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_runtime import CommandReceipt, parse_command
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

from ..persistence.commands import CommandConflict
from .model import TransitionError


def install_admission(app, admission, credentials):
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
