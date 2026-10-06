import asyncio

from amphora_contracts_core import Identifier
from amphora_contracts_execution_proofs import AcceptedToolExecution
from fastapi import Request
from fastapi.responses import JSONResponse

from .projection import ProducerProofError
from .reads import ExecutionProofs


def install(app, history, credentials):
    proofs = ExecutionProofs(history.engine)

    @app.exception_handler(ProducerProofError)
    async def integrity_failure(_request, _error):
        return JSONResponse(status_code=503,content={'reason_code':'producer_integrity_unavailable'},headers={'Cache-Control':'no-store'})

    @app.get('/v1/runs/{run_id}/completions/{completion_id}/producer',response_model=AcceptedToolExecution)
    async def producer(run_id: Identifier, completion_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get('authorization'))
        proof = await asyncio.to_thread(proofs.read,principal,run_id,completion_id)
        return JSONResponse(content=proof.model_dump(mode='json'),headers={'Cache-Control':'no-store'})
