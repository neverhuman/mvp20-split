"""Map owner command disposition to the public runtime receipt."""

from dataclasses import dataclass

from amphora_contracts_runtime import CommandReceipt


@dataclass(frozen=True, slots=True)
class RuntimeReply:
    command: object
    operation_id: str

    def _receipt(self, outcome):
        binding = {"identity": self.command.identity.model_dump(), "request_sha256": self.command.sha256,
                   "operation_id": self.operation_id}
        return CommandReceipt.model_validate({"outcome": {"binding": binding, **outcome}})

    def reject(self, reason):
        return self._receipt({"status": "rejected", "reason_code": reason})

    def pending(self):
        return self._receipt({"status": "pending"})

    def accepted(self, kind, object_id, revision):
        return self._receipt({"status": "accepted", "committed": {
            "kind": kind, "object_id": object_id, "revision": revision}})
