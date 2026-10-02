"""Bounded authenticated graph proposals and exact immutable reads."""

import asyncio
import json

from amphora_contracts_core import Identifier
from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    DomainGraphRef,
    DomainGraphSnapshot,
    DomainHead,
    DomainRevisionRef,
    GraphAuthoringProfile,
    GraphChangeDecision,
    GraphChangeProposal,
    GraphProposalStatus,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..authoring.canonical import KnowledgeError
from ..validation.transport import PeerUnavailable, strict_json


def reply(code, status):
    return JSONResponse({"code": code}, status_code=status, headers={"Cache-Control": "no-store"})


async def body(request):
    parts, size = [], 0
    async for part in request.stream():
        size += len(part)
        if size > 262144:
            raise KnowledgeError("request_limit")
        parts.append(part)
    return b"".join(parts)


def create_app(workflow, credentials):
    app = FastAPI(title="Amphora Knowledge structural authoring", docs_url=None, redoc_url=None, openapi_url=None)
    ledger = workflow.ledger

    @app.get("/health")
    def health():
        return {"service": "knowledge", "authority": "structural_only"}

    async def invoke(request, model, operation, query_factory=None):
        try:
            principal = credentials.authenticate(request.headers.get("authorization"))
            if query_factory is None:
                if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                    return reply("json_required", 415)
                raw = await asyncio.wait_for(body(request), timeout=5)
                try:
                    value = strict_json(raw)
                    query = model.model_validate_json(json.dumps(value, allow_nan=False))
                except (ValueError, RecursionError):
                    return reply("invalid_request", 422)
            else:
                query = query_factory(principal)
            result = await asyncio.to_thread(operation, principal, query)
            if result is None:
                return reply("graph_record_unavailable", 404)
            return JSONResponse(result.model_dump(mode="json"), headers={"Cache-Control": "no-store"})
        except PeerUnavailable:
            return reply("reference_review_pending", 503)
        except SQLAlchemyError:
            return reply("knowledge_owner_unavailable", 503)
        except KnowledgeError as error:
            code = str(error)
            status = 401 if code == "unauthorized" else 403 if code == "access_denied" else 413 if code == "request_limit" else 409
            if code.endswith("storage_mismatch") or code.startswith("stored_"):
                return reply("knowledge_owner_unavailable", 503)
            return reply(code, status)
        except TimeoutError:
            return reply("request_timeout", 408)
        except (ValueError, RecursionError):
            return reply("knowledge_owner_unavailable", 503)

    @app.post("/v1/graph-proposals", response_model=GraphChangeDecision)
    async def propose(request: Request):
        return await invoke(request, GraphChangeProposal, workflow.submit)

    @app.get("/v1/graphs/{graph_id}/proposals/{change_id}", response_model=GraphProposalStatus)
    async def status(graph_id: Identifier, change_id: Identifier, request: Request):
        return await invoke(request, None, lambda principal, graph: ledger.status(principal, graph, change_id),
            lambda principal: DomainGraphRef(scope=principal.scope, graph_id=graph_id))

    @app.post("/v1/graph-heads/read", response_model=DomainHead)
    async def head(request: Request):
        return await invoke(request, DomainGraphRef, ledger.head)

    @app.post("/v1/graph-snapshots/read", response_model=DomainGraphSnapshot)
    async def snapshot(request: Request):
        return await invoke(request, DomainRevisionRef, ledger.snapshot)

    @app.post("/v1/graph-changes/read", response_model=AcceptedGraphChange)
    async def change(request: Request):
        return await invoke(request, AcceptedChangeRef, ledger.change)

    @app.post("/v1/graph-profiles/read", response_model=GraphAuthoringProfile)
    async def profile(request: Request):
        return await invoke(request, DomainGraphRef, ledger.profile)

    return app
