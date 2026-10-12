"""Approved authenticated intake only; the HTTP request never verifies evidence."""
import asyncio
from typing import Annotated

from amphora_contracts_campaign_curation import CapabilityFulfillmentReceipt
from amphora_contracts_core import Identifier
from fastapi import Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..access import Principal
from ..context.policy import require
from ..curation_intake.commands import FulfillmentCommand
from ..curation_intake.record import encoded


def install_fulfillments(app, journal, credentials):
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if request.query_params:
            raise ValueError('unexpected_query')
        return credentials.authenticate(request.headers.get('authorization'))

    @app.post('/v1/capability-requests/{request_id}/fulfillments', response_model=CapabilityFulfillmentReceipt)
    async def submit(request: Request, request_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        try:
            raw = await request.body()
            command = FulfillmentCommand.bind(principal, raw)
            require(command.request.payload.request.request_id == request_id, 'fulfillment_path_mismatch')
            result = await asyncio.to_thread(journal.receive, principal, raw)
        except ValueError as error:
            reason = str(error)
            if reason == 'capability_request_not_found':
                status, code = 404, reason
            elif reason == 'fulfillment_command_conflict':
                status, code = 409, reason
            elif reason.startswith(('stored_', 'capability_original_', 'fulfillment_original_')):
                status, code = 409, 'fulfillment_history_inconsistent'
            else:
                status, code = 422, 'invalid_fulfillment_request'
            return JSONResponse({'reason_code': code}, status_code=status, headers={'Cache-Control': 'no-store'})
        return Response(encoded(result), media_type='application/json', headers={'Cache-Control': 'no-store'})
