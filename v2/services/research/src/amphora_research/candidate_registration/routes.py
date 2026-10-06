from amphora_contracts_research import CandidateRevision, CandidateRevisionRef
from fastapi import Request


def install_routes(app, invoke, reader, registrar):
    @app.post("/v1/candidates/read", response_model=CandidateRevision)
    async def read_candidate(request: Request):
        return await invoke(request, CandidateRevisionRef, reader.read)

    if registrar is not None:

        @app.post("/v1/candidates", response_model=CandidateRevision)
        async def declare_candidate(request: Request):
            return await invoke(
                request, CandidateRevision, registrar.register, limit=262144
            )
