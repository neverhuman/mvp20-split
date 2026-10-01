"""Bounded authenticated read API; no identity creation or scientific acceptance."""

import asyncio
import json

from amphora_contracts_research import IdentityResolution, ResolveIdentity
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..identity.questions import ResearchIdentityError
from .access import AccessDenied


class InvalidRequest(ValueError):
    pass


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidRequest("duplicate_json_key")
        result[key] = value
    return result


def _constant(_value):
    raise InvalidRequest("invalid_json_constant")


async def _body(request):
    parts = []
    count = 0
    async for part in request.stream():
        count += len(part)
        if count > 16384:
            raise InvalidRequest("request_limit")
        parts.append(part)
    return b"".join(parts)


def create_app(resolver, credentials):
    app = FastAPI(title="Amphora Research identity reads", docs_url=None, redoc_url=None)

    @app.get("/health")
    def health():
        return {"service": "research", "authority": "identity_only"}

    @app.post("/v1/identities/resolve", response_model=IdentityResolution)
    async def resolve(request: Request):
        try:
            principal = credentials.authenticate(request.headers.get("authorization"))
            if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                return JSONResponse(status_code=415, content={"code": "json_required"})
            body = await asyncio.wait_for(_body(request), timeout=5)
            decoded = json.loads(body.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
            # Parse in JSON mode so immutable tuple/schema rules match published wire contracts.
            query = ResolveIdentity.model_validate_json(json.dumps(decoded))
            return await asyncio.to_thread(resolver.resolve, principal, query)
        except AccessDenied as error:
            status = 401 if str(error) == "unauthorized" else 403
            return JSONResponse(status_code=status, content={"code": str(error)})
        except InvalidRequest as error:
            return JSONResponse(status_code=413 if str(error) == "request_limit" else 422, content={"code": str(error)})
        except (SQLAlchemyError, ResearchIdentityError):
            return JSONResponse(status_code=503, content={"code": "identity_owner_unavailable"})
        except (ValueError, UnicodeError, RecursionError, ValidationError):
            return JSONResponse(status_code=422, content={"code": "invalid_request"})
        except TimeoutError:
            return JSONResponse(status_code=408, content={"code": "request_timeout"})

    return app
