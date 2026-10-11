"""Exact scoped read only; no provider, compilation, backfill or write endpoint."""

import asyncio
import re
from typing import Annotated

from amphora_contracts_planning import CampaignOriginDraft, CampaignOriginV2
from fastapi import Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..access import Principal


def install_campaign_origins(app, reader, credentials):
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        principal = credentials.authenticate(request.headers.get('authorization'))
        principal.require('read_campaign_origin', principal.scope)
        return principal

    @app.get('/v1/campaign-origins/{draft_id}', response_model=CampaignOriginV2)
    async def campaign_origin(request: Request, draft_id: str, revision: str, content_sha256: str,
                              principal: Annotated[Principal, Depends(authorized)]):
        pairs = list(request.query_params.multi_items())
        if (len(pairs) != 2 or {key for key, _ in pairs} != {'revision', 'content_sha256'} or
                not re.fullmatch(r'[1-9][0-9]{0,15}', revision) or await request.body()):
            return JSONResponse({'reason_code': 'invalid_campaign_origin_request'}, status_code=422)
        try:
            draft = CampaignOriginDraft(scope=principal.scope, draft_id=draft_id,
                                        revision=int(revision), content_sha256=content_sha256)
        except ValueError:
            return JSONResponse({'reason_code': 'invalid_campaign_origin_request'}, status_code=422)
        try:
            result = await asyncio.to_thread(reader.read, principal, draft)
        except ValueError as error:
            if str(error) == 'origin_response_limit':
                return JSONResponse({'reason_code': 'campaign_origin_response_limit'}, status_code=422)
            return JSONResponse({'reason_code': 'campaign_origin_inconsistent'}, status_code=409)
        if result is None:
            return JSONResponse({'reason_code': 'campaign_origin_not_recorded'}, status_code=404)
        return Response(result.canonical, media_type='application/json', headers={'Cache-Control': 'no-store'})
