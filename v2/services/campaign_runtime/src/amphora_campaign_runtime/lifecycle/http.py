"""Explicitly configured synthetic admission routes; no general graph activation."""

import asyncio

from amphora_contracts_artifacts import ReservationBinding, RuntimeOutcome
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_runtime import ClaimResponse, CommandReceipt, RunSnapshot, parse_command
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..completion.artifacts import ReservationUnavailable
from ..completion.retention import IntentOutcomes
from ..persistence.commands import CommandConflict
from .authority import AuthorityCommands
from .claims import RuntimeLeases
from .model import TransitionError
from .reads import RuntimeReads


def install_admission(app, admission, credentials, completion=None):
    leases = RuntimeLeases(admission.commands.engine)
    authority = AuthorityCommands(admission.commands.engine)
    reads = RuntimeReads(admission.commands.engine)
    @app.exception_handler(TransitionError)
    async def denied(_request, error):
        status = {"unauthenticated": 401, "run_unavailable": 404}.get(str(error), 403)
        return JSONResponse({"reason_code": str(error)}, status_code=status)

    @app.get("/ready")
    def ready():
        with admission.commands.engine.connect() as conn:
            conn.execute(text("SELECT operation_id FROM runtime.policy_outbox LIMIT 0"))
        return {"status": "ready", "mode": "fixture_lifecycle"}

    @app.get("/v1/runs/{run_id}", response_model=RunSnapshot)
    async def read_run(run_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reads.run, principal, run_id)

    @app.exception_handler(CommandEncodingError)
    async def malformed(_request, _error):
        return JSONResponse({"reason_code": "invalid_command"}, status_code=422)

    @app.exception_handler(CommandConflict)
    async def conflict(_request, _error):
        return JSONResponse({"reason_code": "command_identity_conflict"}, status_code=409)

    @app.exception_handler(DBAPIError)
    async def unavailable(_request, _error):
        return JSONResponse({"reason_code": "persistence_unavailable"}, status_code=503)

    @app.exception_handler(ReservationUnavailable)
    async def reservation_unavailable(_request, _error):
        return JSONResponse({"reason_code": "reservation_unavailable"}, status_code=503)

    if completion is not None:
        outcomes = IntentOutcomes(admission.commands.engine, completion.artifacts.owner)

        @app.post("/v1/completion-intents/outcome", response_model=RuntimeOutcome)
        async def intent_outcome(request: Request):
            principal = credentials.authenticate(request.headers.get("authorization"))
            try:
                binding = ReservationBinding.model_validate_json(await request.body())
            except ValidationError as error:
                raise RequestValidationError(error.errors()) from None
            return await asyncio.to_thread(outcomes.lookup, principal, binding)

        @app.post("/v1/invocations/complete", response_model=CommandReceipt)
        async def complete(request: Request):
            principal = credentials.authenticate(request.headers.get("authorization"))
            command = parse_command("runtime.complete", await request.body())
            return await asyncio.to_thread(completion.complete, principal, command)

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
