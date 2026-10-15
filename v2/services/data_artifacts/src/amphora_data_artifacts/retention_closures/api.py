"""Scoped additive closure reservation routes; no worker authority grant."""

import asyncio

from amphora_contracts_artifact_retention import DerivedClosureReservationReceipt, parse_derived_closure_command
from amphora_contracts_core import Identifier
from fastapi import Request

from .reservations import ClosureReservations


def install(app, uploads, outcomes, credentials, command_body):
    reservations = ClosureReservations(uploads, outcomes)

    @app.post("/v1/retention-closures/reserve", response_model=DerivedClosureReservationReceipt)
    async def reserve_derived_closure(request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        command = parse_derived_closure_command(await command_body(request))
        return await asyncio.to_thread(reservations.reserve, principal, command)

    @app.get("/v1/retention-closures/{reservation_id}", response_model=DerivedClosureReservationReceipt)
    async def read_derived_closure(reservation_id: Identifier, request: Request):
        principal = credentials.authenticate(request.headers.get("authorization"))
        return await asyncio.to_thread(reservations.get, principal, reservation_id)
