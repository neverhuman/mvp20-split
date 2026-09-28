"""Identity transport only; authenticating actor/scope remains the handler's job."""

from typing import Literal

from amphora_contracts_core import Identifier, Scope, WireModel


class CommandIdentity(WireModel):
    schema_version: Literal["1"] = "1"
    command_family: Identifier
    command_id: Identifier
    scope: Scope
    actor_id: Identifier
