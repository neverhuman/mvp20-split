"""Approved scoped read-only metadata GET; existing grants and error handling."""
import asyncio
from amphora_contracts_artifact_ancestry import ArtifactAncestryFootprint
from amphora_contracts_core import Identifier
from fastapi import Request,Response
from .inspection import AncestryFootprints


class AncestryNoStore:
    """Pass through legacy ASGI calls unchanged, including stream cancellation."""
    def __init__(self,app):self.app=app

    async def __call__(self,scope,receive,send):
        path=scope.get("path","")
        if scope["type"]!="http" or not (path.startswith("/v1/artifacts/") and path.endswith("/ancestry-footprint")):
            await self.app(scope,receive,send)
            return
        async def no_store(message):
            if message["type"]=="http.response.start":
                message={**message,"headers":[(key,value) for key,value in message.get("headers",[])
                    if key.lower()!=b"cache-control"]+[(b"cache-control",b"no-store")]}
            await send(message)
        await self.app(scope,receive,no_store)


def install(app,engine,credentials):
    service=AncestryFootprints(engine)
    app.add_middleware(AncestryNoStore)

    @app.get("/v1/artifacts/{artifact_id}/ancestry-footprint",response_model=ArtifactAncestryFootprint)
    async def footprint(artifact_id:Identifier,request:Request,response:Response):
        response.headers["Cache-Control"]="no-store"
        principal=credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(service.get,principal,artifact_id)
