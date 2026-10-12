"""Bounded curation intake and read-only recovery; scheduling belongs to a worker."""
import asyncio
import json
from typing import Annotated

from amphora_contracts_campaign_curation import CurationReceipt, CurationReceiptQuery, CurationView
from amphora_contracts_core import Identifier
from fastapi import Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..access import Principal
from ..context.snapshot import _constant, _object
from .record import encoded


def _response(value, absent):
    if value is None:
        return JSONResponse({'reason_code': absent}, status_code=404, headers={'Cache-Control': 'no-store'})
    return Response(encoded(value), media_type='application/json', headers={'Cache-Control': 'no-store'})


def _error(error):
    if str(error) in {'curation_command_conflict', 'curation_receipt_conflict'}:
        return JSONResponse({'reason_code': str(error)}, status_code=409)
    if str(error).startswith('stored_curation_'):
        return JSONResponse({'reason_code': 'curation_history_inconsistent'}, status_code=409)
    return JSONResponse({'reason_code': 'invalid_curation_request'}, status_code=422)


def install_curations(app, journal, credentials):
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if request.query_params:
            raise ValueError('unexpected_query')
        return credentials.authenticate(request.headers.get('authorization'))

    @app.post('/v1/campaign-curations', response_model=CurationReceipt)
    async def submit(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        try:
            value = await asyncio.to_thread(journal.receive, principal, await request.body())
        except ValueError as error:
            return _error(error)
        return _response(value, 'curation_not_recorded')

    @app.post('/v1/campaign-curations/receipts/query', response_model=CurationReceipt)
    async def receipt(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        try:
            raw = json.loads(await request.body(), object_pairs_hook=_object, parse_constant=_constant)
            query = CurationReceiptQuery.model_validate_json(json.dumps(raw))
            value = await asyncio.to_thread(journal.receipt, principal, query)
        except (ValueError, UnicodeError) as error:
            return _error(error)
        return _response(value, 'curation_receipt_not_recorded')

    @app.get('/v1/campaign-curations/{curation_id}', response_model=CurationView)
    async def read(request: Request, curation_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        if await request.body():
            return JSONResponse({'reason_code': 'invalid_curation_request'}, status_code=422)
        try:
            value = await asyncio.to_thread(journal.read, principal, curation_id)
        except ValueError as error:
            return _error(error)
        return _response(value, 'curation_not_recorded')
