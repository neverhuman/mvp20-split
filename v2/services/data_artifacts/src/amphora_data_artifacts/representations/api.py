"""Opt-in authenticated profile, encoding and current binding HTTP operations."""

import asyncio
import json

from amphora_contracts_core import Digest, Identifier
from amphora_contracts_representations import (
    EncodeSourceRequest,
    EncodingProfile,
    EncodingProfileRef,
    EncodingStatus,
    RepresentationBinding,
)
from fastapi import APIRouter, HTTPException, Request, Response

from ..acquisition.provenance import ProvenanceError
from ..publication.schemas import json_value
from .validation import RepresentationError


def representation_router(service, credentials):
    router = APIRouter(prefix="/v1/representations")

    def principal_for(request, *actions):
        principal = credentials.authenticate(request.headers.get("authorization"))
        for action in actions:
            principal.require(action)
        return principal

    async def body(request, model):
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            raise HTTPException(415, detail="json_required")
        raw = bytearray()
        try:
            async with asyncio.timeout(5):
                async for chunk in request.stream():
                    if len(raw) + len(chunk) > 65536:
                        raise HTTPException(413, detail="request_limit")
                    raw.extend(chunk)
            return model.model_validate_json(
                json.dumps(json_value(bytes(raw)), ensure_ascii=False, allow_nan=False)
            )
        except (ValueError, UnicodeError, RecursionError) as error:
            raise HTTPException(422, detail="invalid_representation_request") from error
        except TimeoutError as error:
            raise HTTPException(408, detail="request_incomplete") from error

    async def owned(operation, *args):
        try:
            return await asyncio.to_thread(operation, *args)
        except ProvenanceError as error:
            raise HTTPException(409, detail=str(error)) from error
        except RepresentationError as error:
            reason = str(error)
            status = (
                404 if reason in {"representation_profile_missing", "representation_binding_missing"} else 409
            )
            if reason in {"representation_encoder_unavailable", "representation_context_unavailable"}:
                status = 422
            raise HTTPException(status, detail=reason) from error

    @router.get("/available-profiles", response_model=tuple[EncodingProfile, ...])
    async def available(request: Request, response: Response):
        principal = principal_for(request, "representation_read")
        response.headers["Cache-Control"] = "no-store"
        return await owned(service.available_profiles, principal)

    @router.post("/profiles", response_model=EncodingProfileRef)
    async def register(request: Request, response: Response):
        principal = principal_for(request, "representation_manage")
        response.headers["Cache-Control"] = "no-store"
        profile = await body(request, EncodingProfile)
        return await owned(service.register, principal, profile)

    @router.get("/profiles/{profile_id}/{version}", response_model=EncodingProfile)
    async def profile(
        profile_id: Identifier, version: Identifier, sha256: Digest, request: Request, response: Response
    ):
        principal = principal_for(request, "representation_read")
        response.headers["Cache-Control"] = "no-store"
        ref = EncodingProfileRef(scope=principal.scope, profile_id=profile_id, version=version, sha256=sha256)
        return await owned(service.profile, principal, ref)

    @router.post("/encodings", response_model=EncodingStatus)
    async def encode(request: Request, response: Response):
        principal = principal_for(
            request,
            "representation_encode",
            "representation_read",
            "read",
            "source_history",
            "upload",
            "finalize",
        )
        response.headers["Cache-Control"] = "no-store"
        command = await body(request, EncodeSourceRequest)
        result = await owned(service.workflow.encode, principal, command)
        response.status_code = 202 if result.outcome.state == "pending" else 200
        return result

    @router.get("/encodings/{encoding_id}", response_model=EncodingStatus)
    async def encoding_status(encoding_id: Identifier, request: Request, response: Response):
        principal = principal_for(request, "representation_read")
        response.headers["Cache-Control"] = "no-store"
        result = await owned(service.workflow.requests.read, principal, encoding_id)
        if result is None:
            raise HTTPException(404, detail="representation_request_missing")
        return result

    @router.get("/bindings/{binding_id}", response_model=RepresentationBinding)
    async def binding(binding_id: Identifier, request: Request, response: Response):
        principal = principal_for(request, "representation_read", "read")
        response.headers["Cache-Control"] = "no-store"
        return await owned(service.bindings.read, principal, binding_id)

    return router
