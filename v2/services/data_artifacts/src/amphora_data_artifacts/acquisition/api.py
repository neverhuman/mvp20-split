"""Opt-in staged ingestion HTTP routes; no automatic publication or peer retry."""

import asyncio
import json

from amphora_contracts_core import Identifier, SafePositiveInt
from amphora_contracts_evidence import (
    ConversionTrace,
    ConversionTraceRef,
    ObserveSourceIdentity,
    PreparedSource,
    RetainPreparedSource,
    SourceIdentityObservation,
    SourceIdentityStatus,
    SourceRevision,
    SourceRightsRevision,
)
from fastapi import APIRouter, HTTPException, Request, Response

from ..publication.schemas import json_value
from .provenance import ProvenanceError
from .research import ResearchLookupError


def acquisition_router(workflow, credentials):
    router = APIRouter(prefix="/v1/acquisition")

    async def body(request, model):
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            raise HTTPException(415, detail="json_required")
        raw = bytearray()
        try:
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    if len(raw) + len(chunk) > 262144:
                        raise HTTPException(413, detail="request_limit")
                    raw.extend(chunk)
            value = json_value(bytes(raw))
            return model.model_validate_json(json.dumps(value, ensure_ascii=False, allow_nan=False))
        except (ValueError, UnicodeError, RecursionError) as error:
            raise HTTPException(422, detail="invalid_acquisition_request") from error
        except TimeoutError as error:
            raise HTTPException(408, detail="request_incomplete") from error

    async def owned(operation, *args):
        try:
            return await asyncio.to_thread(operation, *args)
        except ProvenanceError as error:
            raise HTTPException(409, detail=str(error)) from error
        except ResearchLookupError as error:
            raise HTTPException(503, detail=str(error)) from error

    def principal_for(request, action):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require(action)
        return principal

    @router.post("/prepare", response_model=PreparedSource)
    async def prepare(request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "acquire")
        principal.require("read")
        source = await body(request, SourceRevision)
        result = await owned(workflow.prepare, principal, source)
        return result.response()

    @router.post("/retain", response_model=ConversionTraceRef)
    async def retain(request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "acquire")
        principal.require("read")
        command = await body(request, RetainPreparedSource)
        return await owned(workflow.retain, principal, command.source, command.trace_id, command.output)

    @router.get("/traces/{trace_id}", response_model=ConversionTrace)
    async def history(trace_id: Identifier, request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "source_history")
        result = await owned(workflow.ledger.trace_history, principal, trace_id)
        if result is None:
            raise HTTPException(404, detail="trace_unavailable")
        return result

    @router.post("/identity-observations", response_model=SourceIdentityObservation)
    async def observe(request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "acquire")
        principal.require("read")
        command = await body(request, ObserveSourceIdentity)
        return await owned(workflow.observe, principal, command)

    @router.get("/identity-observations/{observation_id}", response_model=SourceIdentityStatus)
    async def observation_history(observation_id: Identifier, request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "source_history")
        result = await owned(workflow.observations.history, principal, observation_id)
        if result is None:
            raise HTTPException(404, detail="observation_unavailable")
        return result

    @router.post("/rights", response_model=SourceRightsRevision)
    async def publish_rights(request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "manage_source_rights")
        record = await body(request, SourceRightsRevision)
        return await owned(workflow.rights.publish, principal, record)

    @router.get("/rights/{rights_id}/{revision}", response_model=SourceRightsRevision)
    async def rights_history(rights_id: Identifier, revision: SafePositiveInt, request: Request, response: Response):
        response.headers["Cache-Control"] = "no-store"
        principal = principal_for(request, "source_history")
        record = await owned(workflow.rights.history, principal, rights_id, revision)
        if record is None:
            raise HTTPException(404, detail="rights_unavailable")
        return record

    return router
