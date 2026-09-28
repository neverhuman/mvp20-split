"""Test-owned recovery manifests; no credentials, owner SQL or inferred success."""

import hashlib
import json
from datetime import datetime


class ScenarioEvidence:
    def __init__(self, case, scope, packages, timeout_seconds):
        if case not in {f"REC-{n:02}" for n in range(1, 10)} or not 0 < timeout_seconds <= 180:
            raise ValueError("Named case and bounded deadline required")
        if set(scope) != {"tenant_id", "project_id"} or not packages:
            raise ValueError("Exact scope and package revisions required")
        self.record = {"case": case, "scope": scope, "packages": packages, "timeout_seconds": timeout_seconds,
                       "identities": {}, "events": [], "status": "incomplete"}

    def identify(self, **identities):
        if identities.keys() - {"run", "activation", "attempt", "intent", "artifact", "upload", "command", "reservation", "operation"}:
            raise ValueError("Only public identities belong in evidence")
        for key, value in identities.items():
            if not isinstance(value, str) or not value:
                raise ValueError("Nonempty identity required")
            self.record["identities"].setdefault(key, [])
            if value not in self.record["identities"][key]:
                self.record["identities"][key].append(value)

    def event(self, kind, detail):
        if kind not in {"barrier", "kill", "restart", "observation", "failure"}:
            raise ValueError("Unknown evidence event")
        self.record["events"].append({"at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                      "kind": kind, "detail": detail})

    def finish(self):
        kinds = {event["kind"] for event in self.record["events"]}
        required = {"barrier", "observation"}
        if self.record["case"] != "REC-05":
            required |= {"kill", "restart"}
        if "failure" in kinds or not required <= kinds or not self.record["identities"].get("command"):
            raise ValueError("Incomplete or failed scenario cannot pass")
        self.record["status"] = "passed"

    def save(self, path):
        body = json.dumps(self.record, sort_keys=True, separators=(",", ":"))
        envelope = {"sha256": hashlib.sha256(body.encode()).hexdigest(), "manifest": self.record}
        path.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
