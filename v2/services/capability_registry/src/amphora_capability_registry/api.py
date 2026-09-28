"""Bounded authenticated registry API; no implicit database migrations."""

from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_core import Digest, Identifier
from amphora_contracts_tools import (
    DeploymentSnapshot,
    RegistryReceipt,
    ReleaseSnapshot,
    parse_registry_command,
)
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from .catalog.model import RegistryDenied

OPERATIONS = frozenset({"register", "activate", "drain", "revoke", "deploy", "drain_deployment", "revoke_deployment", "heartbeat", "resolve"})


def create_app(registry, credentials):
    app = FastAPI(title="Amphora Capability Registry", version="1")

    @app.exception_handler(RegistryDenied)
    async def denied(_, error):
        reason = str(error)
        status = 401 if reason == "authentication_required" else 404 if reason.endswith("not_found") else 409 if reason == "command_identity_conflict" else 403
        return JSONResponse(status_code=status, content={"reason_code": reason})

    @app.exception_handler(CommandEncodingError)
    async def malformed(_, error):
        return JSONResponse(status_code=422, content={"reason_code": str(error)})

    @app.post("/v1/registry/{operation}", response_model=RegistryReceipt)
    async def command(operation: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        if operation not in OPERATIONS:
            raise CommandEncodingError("unknown_family")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 262144:
                raise CommandEncodingError("too_large")
        parsed = parse_registry_command("registry." + operation, bytes(body))
        return await run_in_threadpool(registry.execute, principal, parsed)

    @app.get("/v1/releases/{digest}", response_model=ReleaseSnapshot)
    def release(digest: Digest, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return registry.read_release(principal, digest)

    @app.get("/v1/deployments/{deployment_id}", response_model=DeploymentSnapshot)
    def deployment(deployment_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return registry.read_deployment(principal, deployment_id)

    return app
