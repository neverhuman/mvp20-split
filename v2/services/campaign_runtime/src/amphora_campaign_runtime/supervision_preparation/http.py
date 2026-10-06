"""Explicit supervised admission uses existing immutable command and policy authority."""

import asyncio

from amphora_contracts_runtime import CommandReceipt
from amphora_contracts_supervision import parse_supervised_admission
from fastapi import Request


def install_admission(app, admission, credentials):
    @app.post('/v1/graph-runs/supervised', response_model=CommandReceipt)
    async def admit_supervised(request: Request):
        principal = credentials.authenticate(request.headers.get('authorization'))
        command = parse_supervised_admission(await request.body())
        return await asyncio.to_thread(admission.admit_supervised, principal, command)
