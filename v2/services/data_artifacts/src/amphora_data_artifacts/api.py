"""Authenticated publication, protective retention and scoped retrieval HTTP boundary."""

import asyncio

from amphora_contracts_artifacts import (
    FinalizedReceipt,
    PublicationObservation,
    ReservationReceipt,
    UploadContentReceipt,
    UploadReceipt,
    parse_command,
)
from amphora_contracts_commands import CommandEncodingError
from amphora_contracts_core import ArtifactRef, Identifier
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .persistence.commands import CommandConflict
from .publication.finalize import Finalizer
from .publication.inspection import PublicationHistory
from .publication.model import UploadError
from .reads import ArtifactReads
from .retention.outcomes import OutcomeUnavailable
from .retention.reservations import Reservations


def create_app(uploads, storage, credentials, outcomes=None):
    app = FastAPI(title="Amphora artifact publication", version="0.1.0")
    finalizer = Finalizer(uploads, storage)
    reads = ArtifactReads(uploads.commands.engine, storage, uploads.limits.max_bytes)
    reservations = Reservations(uploads, outcomes)
    publication_history = PublicationHistory(uploads.commands.engine)

    @app.exception_handler(UploadError)
    async def upload_error(_request, error):
        reason = str(error)
        status = 401 if reason == "unauthenticated" else 403 if reason == "access_denied" else 409
        if reason in {"upload_unavailable", "artifact_unavailable", "reservation_unavailable", "command_unavailable"}:
            status = 404
        if reason in {"upload_too_large", "body_too_large", "artifact_read_limit"}:
            status = 413
        return JSONResponse({"reason_code": reason}, status_code=status)

    @app.exception_handler(CommandEncodingError)
    async def encoding_error(_request, _error):
        return JSONResponse({"reason_code": "invalid_command"}, status_code=422)

    @app.exception_handler(CommandConflict)
    async def command_error(_request, _error):
        return JSONResponse({"reason_code": "command_identity_conflict"}, status_code=409)

    @app.exception_handler(DBAPIError)
    async def database_error(_request, _error):
        return JSONResponse({"reason_code": "storage_unavailable"}, status_code=503)

    @app.exception_handler(OSError)
    async def filesystem_error(_request, _error):
        return JSONResponse({"reason_code": "storage_unavailable"}, status_code=503)

    @app.exception_handler(OutcomeUnavailable)
    async def outcome_error(_request, error):
        return JSONResponse({"reason_code": str(error)}, status_code=503)

    @app.post("/v1/reservations", response_model=ReservationReceipt)
    async def reserve(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require("retention")
        command = parse_command("artifacts.reserve", await command_body(request))
        return await asyncio.to_thread(reservations.reserve, principal, command)

    @app.post("/v1/reservations/confirm", response_model=ReservationReceipt)
    async def confirm(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require("retention")
        command = parse_command("artifacts.confirm", await command_body(request))
        return await asyncio.to_thread(reservations.reconcile, principal, command)

    @app.post("/v1/reservations/reconcile", response_model=ReservationReceipt)
    async def reconcile(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require("retention")
        command = parse_command("artifacts.reconcile", await command_body(request))
        return await asyncio.to_thread(reservations.reconcile, principal, command)

    @app.get("/v1/reservations/{reservation_id}", response_model=ReservationReceipt)
    async def reservation(reservation_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reservations.get, principal, reservation_id)

    @app.get("/ready")
    def ready():
        with uploads.commands.engine.connect() as conn:
            conn.execute(text("SELECT created_at FROM artifacts.uploads LIMIT 0"))
        return {"ready": True}

    @app.get("/health")
    def health():
        return {"mode": "verified_publication", "publication_available": True, "retention_available": outcomes is not None}

    @app.get("/v1/commands/{family}/{command_id}", response_model=PublicationObservation)
    async def publication_receipt(family: Identifier, command_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(publication_history.read, principal, family, command_id)

    @app.get("/v1/artifacts/{artifact_id}", response_model=ArtifactRef)
    async def metadata(artifact_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return (await asyncio.to_thread(reads.get, principal, artifact_id)).reference

    @app.get("/v1/artifacts/{artifact_id}/content")
    async def read_content(artifact_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        stored, body = await asyncio.to_thread(reads.content, principal, artifact_id)
        return Response(body, media_type=stored.reference.media_type,
                        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"})

    @app.post("/v1/uploads", response_model=UploadReceipt)
    async def begin(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require("upload")
        command = parse_command("artifacts.begin_upload", await command_body(request))
        return await asyncio.to_thread(uploads.begin, principal, command)

    async def command_body(request):
        body = bytearray()
        try:
            async with asyncio.timeout(uploads.limits.seconds):
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 262144:
                        raise UploadError("body_too_large")
                    body.extend(chunk)
        except TimeoutError as error:
            raise UploadError("upload_timeout") from error
        return bytes(body)

    @app.post("/v1/artifacts/finalize", response_model=FinalizedReceipt)
    async def finalize(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        principal.require("finalize")
        command = parse_command("artifacts.finalize", await command_body(request))
        return await asyncio.to_thread(finalizer.finalize, principal, command)

    @app.put("/v1/uploads/{upload_id}/content", response_model=UploadContentReceipt)
    async def content(upload_id: str, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        attempt = await asyncio.to_thread(uploads.start, principal, upload_id)
        writer = None
        settled = False
        try:
            writer = storage.writer(attempt)
            async with asyncio.timeout(uploads.limits.seconds):
                async for chunk in request.stream():
                    # Bounded local writes are synchronous so cancellation cannot race a writer thread.
                    writer.write(chunk)
            writer.seal()
            writer.close()
            status = await asyncio.to_thread(uploads.finish, principal, attempt,
                                            verified=True, actual_bytes=writer.count)
            settled = True
            if status != "streamed":
                raise UploadError("upload_not_selected")
            return UploadContentReceipt(upload_id=upload_id, attempt_id=attempt.attempt_id,
                                        generation=attempt.generation)
        except TimeoutError as error:
            raise UploadError("upload_timeout") from error
        finally:
            if not settled:
                actual = None
                if writer is not None:
                    try:
                        writer.close()
                        actual = writer.count
                    except OSError:
                        pass  # Keep full allocation when durable byte count is uncertain.
                # If this also fails, the persisted streaming attempt remains conservatively charged.
                await asyncio.shield(asyncio.to_thread(uploads.finish, principal, attempt,
                                                       verified=False, actual_bytes=actual))

    return app
