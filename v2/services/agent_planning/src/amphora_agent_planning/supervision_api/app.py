"""A focused public intake/readback surface, not an execution or provider endpoint."""

import asyncio
from importlib.metadata import version
from typing import Annotated

from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_core import Identifier
from amphora_contracts_supervision import (
    CheckpointExecutionReport,
    CheckpointRequest,
    SupervisionCommandReceipt,
    SupervisionRequest,
    parse_checkpoint_command,
    parse_supervision_command,
)
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from ..access import Principal
from ..supervision_completion import CompletionJournal
from ..supervision_intake.commands import IncomingRequest
from .bounds import RequestBounds
from .credentials import AuthenticationError


def create_app(intake=None, credentials=None, *, topology=None, campaign_origins=None):
    if (intake is None) != (credentials is None):
        raise ValueError('complete_supervision_configuration_required')
    if topology is not None and intake is None:
        raise ValueError('topology_requires_configured_planning')
    if campaign_origins is not None and intake is None:
        raise ValueError('campaign_origins_require_configured_planning')
    if credentials is not None and topology is None and credentials.has_any_action({'propose_topology','read_topology'}):
        raise ValueError('topology_configuration_required')
    app = FastAPI(title='Amphora Planning supervisor intake', version=version("amphora-agent-planning"))
    app.add_middleware(RequestBounds)

    @app.exception_handler(AuthenticationError)
    async def unauthenticated(_request, _error):
        return JSONResponse({'reason_code': 'unauthenticated'}, status_code=401,
                            headers={'WWW-Authenticate': 'Bearer'})

    @app.exception_handler(PermissionError)
    async def denied(_request, _error):
        return JSONResponse({'reason_code': 'planning_access_denied'}, status_code=403)

    @app.exception_handler(DBAPIError)
    async def unavailable(_request, _error):
        return JSONResponse({'reason_code': 'planning_persistence_unavailable'}, status_code=503)

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    @app.exception_handler(CommandEncodingError)
    async def malformed(_request, _error):
        if _request.url.path.startswith('/v1/campaign-origins'):
            return JSONResponse({'reason_code': 'invalid_campaign_origin_request'}, status_code=422)
        return JSONResponse({'reason_code': 'invalid_topology_request' if _request.url.path.startswith('/v1/topology-proposals') else 'invalid_supervision_command'}, status_code=422)

    @app.exception_handler(ValueError)
    async def invalid(_request, error):
        reason = str(error)
        if reason in {'supervision_command_conflict', 'receipt_query_conflict', 'supervision_request_profile_mismatch'}:
            return JSONResponse({'reason_code': reason}, status_code=409)
        if reason in {'actor_mismatch', 'supervision_actor_mismatch', 'request_actor_mismatch', 'scope_mismatch'}:
            return JSONResponse({'reason_code': 'planning_access_denied'}, status_code=403)
        return JSONResponse({'reason_code': 'invalid_supervision_binding'}, status_code=422)

    @app.get('/live')
    def live():
        return {'status': 'live'}

    @app.get('/ready')
    def ready():
        if intake is None:
            return JSONResponse({'status': 'not_configured'}, status_code=503)
        with intake.engine.connect() as conn:
            if conn.execute(text('SELECT current_user')).scalar_one() != 'planning_service':
                return JSONResponse({'status': 'role_unavailable'}, status_code=503)
            conn.execute(text('SELECT canonical_bytes FROM planning.checkpoint_execution_reports LIMIT 0'))
            conn.execute(text('SELECT canonical_request FROM planning.supervision_requests LIMIT 0'))
            conn.execute(text('SELECT canonical_receipt FROM planning.supervision_commands LIMIT 0'))
            conn.execute(text('SELECT pointer_bytes FROM planning.campaign_origins LIMIT 0'))
            compatible = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE "
                "conrelid='planning.supervision_commands'::regclass AND conname='supervision_commands_family_check' "
                "AND position('planning.supervision.request.v2' in pg_get_constraintdef(oid)) > 0)")).scalar_one()
            if not compatible:
                return JSONResponse({'status': 'schema_unavailable'}, status_code=503)
        if topology is not None:
            with topology.journal.engine.connect() as conn:
                conn.execute(text('SELECT record_bytes FROM planning.topology_proposals LIMIT 0'))
        return {'status': 'ready', 'mode': 'supervisor_intake_and_topology' if topology is not None else 'supervisor_intake_only'}

    if intake is None:
        return app
    from ..campaign_origin.http import install_campaign_origins
    from ..campaign_origin.reader import CampaignOriginReader
    install_campaign_origins(app, campaign_origins if campaign_origins is not None else CampaignOriginReader(intake.engine), credentials)
    if topology is not None:
        from ..topology.http import install_topology
        install_topology(app,topology,credentials)
    bearer = HTTPBearer(auto_error=False)

    def authorized(request: Request, _credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if request.query_params:
            raise ValueError('unexpected_query')
        return credentials.authenticate(request.headers.get('authorization'))

    @app.post('/v1/supervision/requests', response_model=SupervisionCommandReceipt)
    async def record(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        command = parse_supervision_command('planning.supervision.request', await request.body())
        return await asyncio.to_thread(intake.receive, principal, command)

    @app.post('/v1/supervision/receipts/query', response_model=SupervisionCommandReceipt)
    async def receipt(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        command = parse_supervision_command('planning.supervision.request', await request.body())
        IncomingRequest.bind(principal, command)
        result = await asyncio.to_thread(intake.receipt, principal, command.identity.command_id)
        if result is None:
            return JSONResponse({'reason_code': 'supervision_receipt_unavailable'}, status_code=404)
        if result.outcome.binding.identity != command.identity or result.outcome.binding.request_sha256 != command.sha256:
            raise ValueError('receipt_query_conflict')
        return result

    @app.get('/v1/supervision/requests/{engagement_id}', response_model=SupervisionRequest)
    async def read(engagement_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        result = await asyncio.to_thread(intake.request, principal, engagement_id)
        if result is None:
            return JSONResponse({'reason_code': 'supervision_request_unavailable'}, status_code=404)
        if result.document().schema_version != '1':
            raise ValueError('supervision_request_profile_mismatch')
        return result.document()

    @app.post('/v2/supervision/requests', response_model=SupervisionCommandReceipt)
    async def record_checkpoint(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        command = parse_checkpoint_command(await request.body())
        return await asyncio.to_thread(intake.receive, principal, command)

    @app.post('/v2/supervision/receipts/query', response_model=SupervisionCommandReceipt)
    async def checkpoint_receipt(request: Request, principal: Annotated[Principal, Depends(authorized)]):
        command = parse_checkpoint_command(await request.body())
        IncomingRequest.bind(principal, command)
        result = await asyncio.to_thread(intake.receipt, principal, command.identity.command_id,
                                         family=command.identity.command_family)
        if result is None:
            return JSONResponse({'reason_code': 'supervision_receipt_unavailable'}, status_code=404)
        if result.outcome.binding.identity != command.identity or result.outcome.binding.request_sha256 != command.sha256:
            raise ValueError('receipt_query_conflict')
        return result

    @app.get('/v2/supervision/requests/{engagement_id}', response_model=CheckpointRequest)
    async def read_checkpoint(engagement_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        result = await asyncio.to_thread(intake.request, principal, engagement_id)
        if result is None:
            return JSONResponse({'reason_code': 'supervision_request_unavailable'}, status_code=404)
        if result.document().schema_version != '2':
            raise ValueError('supervision_request_profile_mismatch')
        return result.document()

    @app.get('/v2/supervision/execution/{engagement_id}', response_model=CheckpointExecutionReport)
    async def execution_report(engagement_id: Identifier, principal: Annotated[Principal, Depends(authorized)]):
        result = await asyncio.to_thread(CompletionJournal(intake.engine).read, principal, engagement_id)
        if result is None:
            return JSONResponse({'reason_code': 'checkpoint_execution_unresolved'}, status_code=404)
        return result.report.document()

    return app
