from amphora_contracts_evaluation_reuse import ReuseProjection, ReuseRequest, ReuseSelection
from fastapi import Request


def install_routes(app, invoke, operations):
    if operations is None:
        return

    @app.post('/v1/evaluation-reuse',response_model=ReuseProjection)
    async def qualify(request: Request):
        return await invoke(request,ReuseRequest,operations.qualify,limit=262144)

    @app.post('/v1/evaluation-reuse/read',response_model=ReuseProjection)
    async def read(request: Request):
        return await invoke(request,ReuseSelection,operations.read)
