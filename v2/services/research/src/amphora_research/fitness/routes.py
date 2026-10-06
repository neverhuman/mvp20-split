from amphora_contracts_fitness import FitnessProjection, FitnessRequest, FitnessSelection
from fastapi import Request


def install_routes(app, invoke, operations):
    if operations is None:
        return

    @app.post("/v1/fitness", response_model=FitnessProjection)
    async def assemble(request: Request):
        return await invoke(request, FitnessRequest, operations.assemble, limit=262144)

    @app.post("/v1/fitness/read", response_model=FitnessProjection)
    async def read(request: Request):
        return await invoke(request, FitnessSelection, operations.read)
