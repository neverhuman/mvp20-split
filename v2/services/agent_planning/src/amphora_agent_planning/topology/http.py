"""Authenticated proposal publication/history, never compiler or Runtime admission."""
import asyncio
import json
from typing import Annotated
from fastapi import Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from amphora_contracts_core import Identifier
from amphora_contracts_topology_search import TopologyRequest, TopologyProjection
from ..access import Principal
from ..context.snapshot import _object, _constant
from .peers import TopologyPeerUnavailable
from .store import TopologyStoreUnavailable
from .values import TopologyRejected, require


def install_topology(app, operations, credentials):
    bearer=HTTPBearer(auto_error=False)
    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        require(not request.query_params,'topology_query_not_allowed')
        return credentials.authenticate(request.headers.get('authorization'))

    @app.exception_handler(TopologyRejected)
    async def rejected(_request, error):
        code=str(error)
        status=409 if code in {'topology_proposal_conflict','topology_current_parent_changed'} else 404 if code in {'topology_profile_unavailable','topology_peer_record_unavailable'} else 422
        return JSONResponse({'reason_code':code},status_code=status)

    @app.exception_handler(TopologyStoreUnavailable)
    @app.exception_handler(TopologyPeerUnavailable)
    async def unavailable(_request, _error):
        return JSONResponse({'reason_code':'topology_dependency_unavailable'},status_code=503)

    @app.post('/v1/topology-proposals',response_model=TopologyProjection)
    async def propose(request: Request, principal: Annotated[Principal,Depends(authorized)]):
        try:
            value=json.loads(await request.body(),object_pairs_hook=_object,parse_constant=_constant)
            selected=TopologyRequest.model_validate_json(json.dumps(value,allow_nan=False))
        except (ValueError,TypeError,RecursionError) as error:
            raise TopologyRejected('invalid_topology_request') from error
        return await asyncio.to_thread(operations.propose,principal,selected)

    @app.get('/v1/topology-proposals/{proposal_id}',response_model=TopologyProjection)
    async def read(proposal_id: Identifier, principal: Annotated[Principal,Depends(authorized)]):
        result=await asyncio.to_thread(operations.read,principal,proposal_id)
        return JSONResponse({'reason_code':'topology_proposal_unavailable'},status_code=404) if result is None else result
