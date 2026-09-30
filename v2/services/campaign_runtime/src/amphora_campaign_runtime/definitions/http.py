"""Explicit authoring routes; legacy execution receipt schemas remain unchanged."""

import asyncio
from typing import Literal

from amphora_contracts_core import Digest, Identifier, SchemaRef
from amphora_contracts_graph_runtime import (
    DefinitionSchema,
    DefinitionUniverse,
    DraftCommandReceipt,
    DraftPage,
    DraftRevision,
    DraftValidation,
    parse_authoring_command,
)
from fastapi import Query, Request
from fastapi.responses import JSONResponse

from .catalog import DefinitionCatalog
from .commands import DefinitionCommands
from .reads import DefinitionReadError, DefinitionReads
from .validate import DefinitionValidator


def install_definitions(app, engine, credentials, universes=None):
    commands, reads = DefinitionCommands(engine), DefinitionReads(engine)
    validator = DefinitionValidator(engine, universes or {})
    catalog = DefinitionCatalog(universes or {})

    def filters(request, allowed=()):
        if set(request.query_params) - set(allowed):
            raise DefinitionReadError("invalid_draft_query")

    @app.exception_handler(DefinitionReadError)
    async def unavailable(_request, error):
        reason = str(error)
        status = 404 if reason.endswith("unavailable") else 409 if reason == "definition_universe_changed" else 422
        return JSONResponse({"reason_code": reason}, status_code=status)

    @app.get("/v1/definition-universe", response_model=DefinitionUniverse)
    async def universe(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request)
        return await asyncio.to_thread(catalog.universe, principal)

    @app.get("/v1/definition-schemas/{digest}", response_model=DefinitionSchema)
    async def schema(digest: Digest, request: Request, schema_id: Identifier, version: Literal["1"], universe_sha256: Digest):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request, ("schema_id", "version", "universe_sha256"))
        reference = SchemaRef(schema_id=schema_id, version=version, sha256=digest)
        return await asyncio.to_thread(catalog.schema, principal, universe_sha256, reference)

    @app.post("/v1/definition-drafts/save", response_model=DraftCommandReceipt)
    async def save(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request)
        command = parse_authoring_command("definition.save", await request.body())
        return await asyncio.to_thread(commands.save, principal, command)

    @app.post("/v1/definition-drafts/validate", response_model=DraftCommandReceipt)
    async def validate(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request)
        command = parse_authoring_command("definition.validate", await request.body())
        return await asyncio.to_thread(validator.validate, principal, command)

    @app.get("/v1/definition-validations/{validation_id}", response_model=DraftValidation)
    async def validation(validation_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request)
        return await asyncio.to_thread(reads.validation, principal, validation_id)

    @app.get("/v1/definition-drafts", response_model=DraftPage)
    async def page(request: Request, limit: int = Query(20, ge=1, le=50), after: Identifier | None = None):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request, ("limit", "after"))
        return await asyncio.to_thread(reads.page, principal, limit=limit, after=after)

    @app.get("/v1/definition-drafts/{draft_id}", response_model=DraftRevision)
    async def revision(draft_id: Identifier, request: Request, revision: int | None = Query(None, ge=1, le=9007199254740991)):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request, ("revision",))
        return await asyncio.to_thread(reads.revision, principal, draft_id, revision)

    @app.get("/v1/definition-commands/{family}/{command_id}", response_model=DraftCommandReceipt)
    async def receipt(family: Identifier, command_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        filters(request)
        return await asyncio.to_thread(reads.receipt, principal, family, command_id)
