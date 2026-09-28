"""Validation-only API. No run creation, persistence, credentials or execution."""

import json
from typing import Annotated

from amphora_contracts_campaigns import CampaignDefinition
from amphora_contracts_core import Finding, WireModel
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .graph import Graph


class ValidationReport(WireModel):
    structurally_valid: bool
    executable: bool = False
    findings: tuple[Finding, ...]
    pending_checks: tuple[str, ...] = (
        "tool_resolution",
        "scientific_applicability",
        "authority",
        "budget",
        "execution",
    )


class RequestBounds:
    """Bound bytes and nesting before DTO parsing; no raw payload in error responses."""

    def __init__(self, app, max_bytes: int = 262144):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        chunks = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            size += len(chunk)
            if size > self.max_bytes:
                return await JSONResponse({"code": "request_too_large"}, status_code=413)(
                    scope, receive, send
                )
            chunks.append(chunk)
            if not message.get("more_body", False):
                break
        body = b"".join(chunks)
        try:
            if body:
                pending = [(json.loads(body), 0)]
                while pending:
                    value, depth = pending.pop()
                    if depth > 64:
                        raise RecursionError
                    if isinstance(value, dict):
                        pending.extend((v, depth + 1) for v in value.values())
                    elif isinstance(value, list):
                        pending.extend((v, depth + 1) for v in value)
        except RecursionError:
            return await JSONResponse({"code": "nesting_limit"}, status_code=422)(scope, receive, send)
        except (ValueError, UnicodeDecodeError):
            return await JSONResponse({"code": "invalid_json"}, status_code=422)(scope, receive, send)
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": body, "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)


def create_app() -> FastAPI:
    app = FastAPI(title="Amphora runtime foundation", version="0.1.0")
    app.add_middleware(RequestBounds)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request, error):
        return JSONResponse(
            {
                "code": "invalid_contract",
                "errors": [{"location": list(e["loc"]), "code": e["type"]} for e in error.errors()[:20]],
            },
            status_code=422,
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "validation_only", "execution_available": False}

    async def parse_campaign(request: Request) -> CampaignDefinition:
        try:
            # JSON arrays map to immutable tuples in strict JSON mode. Do not
            # route through Python-dict coercion and accidentally change the wire contract.
            return CampaignDefinition.model_validate_json(await request.body())
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from None

    @app.post(
        "/v1/campaign-definitions/validate",
        response_model=ValidationReport,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/CampaignDefinition"}}
                },
            }
        },
    )
    def validate_campaign(definition: Annotated[CampaignDefinition, Depends(parse_campaign)]):
        try:
            issues = Graph.from_contract(definition.body).issues()
        except ValueError:
            return ValidationReport(
                structurally_valid=False,
                findings=(
                    Finding(
                        code="loop_nesting_limit",
                        location="body",
                        message="At most eight nested loops are supported.",
                    ),
                ),
            )
        return ValidationReport(
            structurally_valid=not issues,
            findings=tuple(
                Finding(code=i.code, location=i.location, message=i.message) for i in issues[:100]
            ),
        )

    def openapi():
        if app.openapi_schema is None:
            description = get_openapi(title=app.title, version=app.version, routes=app.routes)
            schema = CampaignDefinition.model_json_schema(ref_template="#/components/schemas/{model}")
            components = description.setdefault("components", {}).setdefault("schemas", {})
            components.update(schema.pop("$defs", {}))
            components["CampaignDefinition"] = schema
            app.openapi_schema = description
        return app.openapi_schema

    app.openapi = openapi
    return app


app = create_app()
