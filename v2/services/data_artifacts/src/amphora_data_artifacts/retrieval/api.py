"""Optional authenticated generation and pinned retrieval HTTP surface."""

import asyncio
import json

from amphora_contracts_core import Digest, Identifier
from amphora_contracts_representations import (
    BuildIndexGeneration,
    IndexGenerationStatus,
    RetrievalRecord,
    RetrieveRepresentations,
)
from fastapi import APIRouter, HTTPException, Request, Response

from ..publication.schemas import json_value
from ..representations.validation import RepresentationError
from ..source_rights.model import RightsError
from .qdrant.transport import QdrantError
from .validation import RetrievalError

BODY_LIMIT = 4 * 1024 * 1024


def retrieval_router(service, credentials):
    router = APIRouter(prefix="/v1/retrieval")

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
                    if len(raw) + len(chunk) > BODY_LIMIT:
                        raise HTTPException(413, detail="request_limit")
                    raw.extend(chunk)
            return model.model_validate_json(
                json.dumps(json_value(bytes(raw)), ensure_ascii=False, allow_nan=False)
            )
        except (ValueError, UnicodeError, RecursionError) as error:
            raise HTTPException(422, detail="invalid_retrieval_request") from error
        except TimeoutError as error:
            raise HTTPException(408, detail="request_incomplete") from error

    async def owned(operation, *args):
        try:
            return await asyncio.to_thread(operation, *args)
        except (RetrievalError, RepresentationError, RightsError) as error:
            reason = str(error)
            status = 409
            if reason in {
                "retrieval_generation_missing",
                "retrieval_binding_missing",
                "retrieval_query_missing",
                "representation_profile_missing",
                "representation_binding_missing",
            }:
                status = 404
            if isinstance(error, RightsError):
                status = 403
            if isinstance(error, QdrantError) or reason in {
                "rights_unavailable",
                "rights_lineage_limit",
                "rights_lineage_cycle",
            }:
                status = 503
            raise HTTPException(status, detail=reason, headers={"Cache-Control": "no-store"}) from error

    @router.post("/generations", response_model=IndexGenerationStatus)
    async def advance(request: Request, response: Response):
        principal = principal_for(request, "representation_manage", "representation_read", "read")
        command = await body(request, BuildIndexGeneration)
        value = await owned(service.advance, principal, command)
        response.headers["Cache-Control"] = "no-store"
        response.status_code = 202 if value.state in {"prepared", "building", "verified"} else 200
        return value

    @router.get("/generations/{corpus_id}/{generation_id}", response_model=IndexGenerationStatus)
    async def generation(
        corpus_id: Identifier, generation_id: Identifier, sha256: Digest, request: Request, response: Response
    ):
        principal = principal_for(request, "representation_read")
        response.headers["Cache-Control"] = "no-store"
        return await owned(service.generation, principal, corpus_id, generation_id, sha256)

    @router.post("/queries", response_model=RetrievalRecord)
    async def retrieve(request: Request, response: Response):
        principal = principal_for(request, "representation_read", "read")
        command = await body(request, RetrieveRepresentations)
        response.headers["Cache-Control"] = "no-store"
        return await owned(service.queries.retrieve, principal, command)

    @router.get("/queries/{retrieval_id}", response_model=RetrievalRecord)
    async def result(retrieval_id: Identifier, request: Request, response: Response):
        principal = principal_for(request, "representation_read", "read")
        response.headers["Cache-Control"] = "no-store"
        return await owned(service.queries.read, principal, retrieval_id)

    return router
