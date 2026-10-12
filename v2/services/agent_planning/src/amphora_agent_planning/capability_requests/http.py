"""Approved read-only capability-request route; no fulfillment or provider effect."""
import asyncio
from typing import Annotated

from amphora_contracts_campaign_curation import CapabilityRequestView
from amphora_contracts_core import Identifier
from fastapi import Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..access import Principal
from ..curation_intake.record import encoded


def install_capability_reads(app, reader, credentials):
    bearer = HTTPBearer(auto_error=False)
    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if request.query_params:
            raise ValueError('unexpected_query')
        return credentials.authenticate(request.headers.get('authorization'))

    @app.get('/v1/capability-requests/{request_id}', response_model=CapabilityRequestView)
    async def read(request: Request, request_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        if await request.body():
            return JSONResponse({'reason_code': 'invalid_capability_request'}, status_code=422)
        try:
            value = await asyncio.to_thread(reader.read, principal, request_id)
        except ValueError:
            return JSONResponse({'reason_code': 'capability_history_inconsistent'}, status_code=409)
        if value is None:
            return JSONResponse({'reason_code': 'capability_request_not_recorded'}, status_code=404,
                headers={'Cache-Control': 'no-store'})
        return Response(encoded(value), media_type='application/json', headers={'Cache-Control': 'no-store'})
