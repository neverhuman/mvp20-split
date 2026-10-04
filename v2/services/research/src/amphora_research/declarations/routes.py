"""Optional public registration routes; existing DTOs remain unchanged."""

from amphora_contracts_research import EvidenceNeed, ResearchQuestion
from fastapi import Request


def install_routes(app, invoke, registrar):
    @app.post("/v1/questions", response_model=ResearchQuestion)
    async def declare_question(request: Request):
        return await invoke(request, ResearchQuestion, registrar.register, limit=262144)

    @app.post("/v1/evidence-needs", response_model=EvidenceNeed)
    async def declare_need(request: Request):
        return await invoke(request, EvidenceNeed, registrar.register, limit=262144)
