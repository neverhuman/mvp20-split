"""Bounded authenticated graph proposals and exact immutable reads."""

import asyncio
import json

from amphora_contracts_core import Identifier
from amphora_contracts_graph_runtime import ReceiptCorrectionView
from amphora_contracts_knowledge import (
    AcceptedChangeRef,
    AcceptedGraphChange,
    CorrectReasoningReceipt,
    DomainGraphRef,
    DomainGraphSnapshot,
    DomainHead,
    DomainRevisionRef,
    GraphAuthoringProfile,
    GraphChangeDecision,
    GraphChangeProposal,
    GraphEntitySearchPage,
    GraphEntitySearchRequest,
    GraphExploreCatalog,
    GraphNeighborhoodPage,
    GraphNeighborhoodRequest,
    GraphObjectDetail,
    GraphObjectRequest,
    GraphProposalStatus,
    GraphRebuildRequest,
    GraphRebuildStatus,
    ReasoningPublicationRequest,
    ReasoningPublicationStatus,
    ReasoningRequest,
    ReasoningStatus,
    SelectReasoningReceipt,
)
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from ..authoring.canonical import KnowledgeError
from ..corrections.boundary import CorrectionBoundary
from ..corrections.store import CorrectionStore
from ..exploration.boundary import ExplorationBoundary
from ..rebuild.boundary import RebuildBoundary
from ..rebuild.store import RebuildStore
from ..rebuild.workflow import RebuildWorkflow
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


def create_app(workflow, credentials, reasoning=None, publication=None):
    app = FastAPI(title="Amphora Knowledge structural authoring", docs_url=None, redoc_url=None, openapi_url=None)
    ledger = workflow.ledger
    exploration = ExplorationBoundary(ledger)
    rebuild = RebuildBoundary(RebuildWorkflow(RebuildStore(ledger.engine)))

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

    @app.post("/v1/graph-explore/catalog", response_model=GraphExploreCatalog)
    async def explore_catalog(request: Request):
        return await invoke(request, DomainRevisionRef, exploration.catalog)

    @app.post("/v1/graph-explore/entities", response_model=GraphEntitySearchPage)
    async def explore_entities(request: Request):
        return await invoke(request, GraphEntitySearchRequest, exploration.search)

    @app.post("/v1/graph-explore/neighborhood", response_model=GraphNeighborhoodPage)
    async def explore_neighborhood(request: Request):
        return await invoke(request, GraphNeighborhoodRequest, exploration.neighborhood)

    @app.post("/v1/graph-explore/object", response_model=GraphObjectDetail)
    async def explore_object(request: Request):
        return await invoke(request, GraphObjectRequest, exploration.detail)

    @app.post("/v1/graph-changes/read", response_model=AcceptedGraphChange)
    async def change(request: Request):
        return await invoke(request, AcceptedChangeRef, ledger.change)

    @app.post("/v1/graph-profiles/read", response_model=GraphAuthoringProfile)
    async def profile(request: Request):
        return await invoke(request, DomainGraphRef, ledger.profile)

    @app.post("/v1/graph-rebuilds", response_model=GraphRebuildStatus)
    async def rebuild_graph(request: Request):
        return await invoke(request, GraphRebuildRequest, rebuild.submit)

    @app.post("/v1/graph-rebuilds/read", response_model=GraphRebuildStatus)
    async def rebuild_status(request: Request):
        return await invoke(request, GraphRebuildRequest, rebuild.read)

    if reasoning is not None:
        @app.post("/v1/graph-reasoning", response_model=ReasoningStatus)
        async def reason(request: Request):
            return await invoke(request, ReasoningRequest, reasoning.submit)

        @app.get("/v1/graphs/{graph_id}/reasoning/{request_id}", response_model=ReasoningStatus)
        async def reason_status(graph_id: Identifier, request_id: Identifier, request: Request):
            return await invoke(request, None, lambda principal, graph: reasoning.read(principal, graph, request_id),
                lambda principal: DomainGraphRef(scope=principal.scope, graph_id=graph_id))

    if publication is not None:
        corrections = CorrectionBoundary(CorrectionStore(ledger.engine))

        @app.post("/v1/reasoning-receipts/correct", response_model=ReceiptCorrectionView)
        async def correct_receipt(request: Request):
            return await invoke(request, CorrectReasoningReceipt, corrections.submit)

        @app.post("/v1/reasoning-receipts/select", response_model=ReceiptCorrectionView)
        async def select_receipt(request: Request):
            return await invoke(request, SelectReasoningReceipt, corrections.read)

        @app.post("/v1/reasoning-publications", response_model=ReasoningPublicationStatus)
        async def publish_reasoning(request: Request):
            return await invoke(request, ReasoningPublicationRequest, publication.submit)

        @app.post("/v1/reasoning-publications/read", response_model=ReasoningPublicationStatus)
        async def publication_status(request: Request):
            return await invoke(request, ReasoningPublicationRequest, publication.read)

    return app
