"""Focused opt-in routes reuse Runtime's existing bounded body/auth/SQL boundary."""

import asyncio
from typing import Annotated

from amphora_contracts_core import Identifier
from amphora_contracts_supervision import (
    CancelSupervision,
    CheckpointDecision,
    SupervisionCommandReceipt,
    SupervisionResponse,
)
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..lifecycle.access import RuntimePrincipal
from ..lifecycle.model import TransitionError
from ..persistence.commands import CommandConflict
from ..supervision_capture import CaptureUnavailable


def install(app, recording, credentials):
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if request.query_params:
            raise HTTPException(422, detail='unexpected_query')
        return credentials.authenticate(request.headers.get('authorization'))

    async def perform(function, *args):
        try:
            result = await asyncio.to_thread(function, *args)
            return JSONResponse({'reason_code': 'supervision_record_unavailable'}, status_code=404) if result is None else result
        except (TransitionError, CommandConflict):
            raise
        except CaptureUnavailable as error:
            status = 403 if str(error) == 'capture_processing_denied' else 503
            return JSONResponse({'reason_code': 'capture_processing_denied' if status == 403 else 'capture_unavailable'}, status_code=status)
        except ValueError as error:
            reason = str(error)
            status = (403 if reason in {'response_actor_mismatch', 'cancellation_actor_mismatch', 'capture_scope_mismatch'} else
                      409 if reason in {'response_command_mismatch', 'cancellation_command_mismatch'} else
                      404 if reason == 'supervision_request_unavailable' else 422)
            return JSONResponse({'reason_code': {403: 'supervision_access_denied', 409: 'supervision_command_conflict',
                404: 'supervision_request_unavailable', 422: 'invalid_supervision_binding'}[status]}, status_code=status)

    @app.get('/v1/supervision/ready')
    def ready():
        return recording.ready()

    @app.get('/v1/supervision/decisions/{run_id}/{decision_id}', response_model=CheckpointDecision)
    async def decision(run_id: Identifier, decision_id: Identifier,
                       principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.decision, principal, run_id, decision_id)

    @app.post('/v1/supervision/responses', response_model=SupervisionCommandReceipt)
    async def respond(request: Request, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.respond, principal, await request.body())

    @app.post('/v1/supervision/cancellations', response_model=SupervisionCommandReceipt)
    async def cancel(request: Request, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.cancel, principal, await request.body())

    @app.post('/v1/supervision/responses/receipts/query', response_model=SupervisionCommandReceipt)
    async def response_receipt(request: Request, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.receipt, principal, 'runtime.supervision.respond', await request.body())

    @app.post('/v1/supervision/cancellations/receipts/query', response_model=SupervisionCommandReceipt)
    async def cancellation_receipt(request: Request, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.receipt, principal, 'runtime.supervision.cancel', await request.body())

    @app.get('/v1/supervision/responses/{response_id}', response_model=SupervisionResponse)
    async def response(response_id: Identifier, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.response, principal, response_id)

    @app.get('/v1/supervision/cancellations/{cancellation_id}', response_model=CancelSupervision)
    async def cancellation(cancellation_id: Identifier, principal: Annotated[RuntimePrincipal, Depends(authorized)]):
        return await perform(recording.cancellation, principal, cancellation_id)
