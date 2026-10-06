"""Opt-in authenticated metadata reads using the existing inspection error protocol."""

import asyncio
from typing import Annotated

from amphora_contracts_core import Digest, Identifier
from amphora_contracts_supervision import (
    CheckpointContextPage,
    CheckpointInspectionPage,
    CheckpointRequestPage,
    CheckpointResponsePage,
)
from fastapi import Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import DBAPIError

from ..inspection.cursors import InspectionError
from ..lifecycle.access import RuntimePrincipal
from ..lifecycle.model import TransitionError
from .reads import SupervisorInspection


def install(app, history, credentials):
    inspection = SupervisorInspection(history.engine, history.cursors)
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        return credentials.authenticate(request.headers.get('authorization'))

    async def perform(request, method, *args, **kwargs):
        names = [key for key, _ in request.query_params.multi_items()]
        allowed = {'limit', 'cursor'} | ({'snapshot_token'} if method != inspection.checkpoints else set())
        if set(names) - allowed or len(names) != len(set(names)):
            raise InspectionError('invalid_page_request')
        try:
            result = await asyncio.to_thread(method, *args, **kwargs)
            if len(result.model_dump_json().encode('utf-8')) > 262144:
                return JSONResponse({'reason_code': 'supervision_inspection_unavailable'}, status_code=503)
            return result
        except TransitionError:
            raise
        except (ValueError, DBAPIError):
            return JSONResponse({'reason_code': 'supervision_inspection_unavailable'}, status_code=503)

    @app.get('/v1/supervision/runs/{run_id}/checkpoints', response_model=CheckpointInspectionPage)
    async def checkpoints(run_id: Identifier, request: Request,
                          principal: Annotated[RuntimePrincipal, Depends(authorized)],
                          limit: int = Query(10, ge=1, le=10), cursor: str | None = Query(None, max_length=4096)):
        return await perform(request, inspection.checkpoints, principal, run_id, limit=limit, cursor=cursor)

    @app.get('/v1/supervision/runs/{run_id}/checkpoints/{decision_id}/requests', response_model=CheckpointRequestPage)
    async def requests(run_id: Identifier, decision_id: Identifier, request: Request,
                       principal: Annotated[RuntimePrincipal, Depends(authorized)],
                       snapshot_token: str = Query(min_length=1, max_length=4096),
                       limit: int = Query(10, ge=1, le=10), cursor: str | None = Query(None, max_length=4096)):
        return await perform(request, inspection.requests, principal, run_id, decision_id,
                             snapshot_token=snapshot_token, limit=limit, cursor=cursor)

    @app.get('/v1/supervision/runs/{run_id}/checkpoints/{decision_id}/requests/{request_sha256}/context',
             response_model=CheckpointContextPage)
    async def context(run_id: Identifier, decision_id: Identifier, request_sha256: Digest, request: Request,
                      principal: Annotated[RuntimePrincipal, Depends(authorized)],
                      snapshot_token: str = Query(min_length=1, max_length=4096),
                      limit: int = Query(10, ge=1, le=10), cursor: str | None = Query(None, max_length=4096)):
        return await perform(request, inspection.context, principal, run_id, decision_id, request_sha256,
                             snapshot_token=snapshot_token, limit=limit, cursor=cursor)

    @app.get('/v1/supervision/runs/{run_id}/checkpoints/{decision_id}/requests/{request_sha256}/responses',
             response_model=CheckpointResponsePage)
    async def responses(run_id: Identifier, decision_id: Identifier, request_sha256: Digest, request: Request,
                        principal: Annotated[RuntimePrincipal, Depends(authorized)],
                        snapshot_token: str = Query(min_length=1, max_length=4096),
                        limit: int = Query(10, ge=1, le=10), cursor: str | None = Query(None, max_length=4096)):
        return await perform(request, inspection.responses, principal, run_id, decision_id, request_sha256,
                             snapshot_token=snapshot_token, limit=limit, cursor=cursor)
