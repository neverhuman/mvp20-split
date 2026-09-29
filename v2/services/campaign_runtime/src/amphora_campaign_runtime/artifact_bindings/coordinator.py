"""Resumable conversion I/O between short, run-locked owner transactions."""

import json
import uuid
from dataclasses import dataclass

from amphora_contracts_artifacts import ReservationReceipt, ReserveArtifact
from sqlalchemy import text

from ..completion.artifacts import ReservationUnavailable, validate_receipt
from ..completion.retention import queue_terminal
from ..coordinator.state import ScopeState, persist_node
from ..coordinator.values import ensure
from ..lifecycle.claims import RUN, SCOPE, RuntimeLeases
from ..lifecycle.model import RunBudget, TransitionError
from .conversion import Conversion
from .model import BindingAddress, BindingInput
from .storage import close, load


@dataclass(frozen=True)
class ConversionWork:
    address: BindingAddress
    binding: BindingInput
    entry: object
    token: str

    @property
    def params(self):
        return {"tenant": self.address.scope.tenant_id, "project": self.address.scope.project_id,
                "run": self.address.run_id, "intent": self.address.identity}


class ProtectedIO:
    def __init__(self, owner, work):
        self.owner, self.work = owner, work

    def guard(self):
        self.owner.leases.commands.transact(lambda conn: self.owner.check(conn, self.work))

    def read(self, reference):
        self.guard()
        return self.owner.publisher.reader.fetch(reference)

    def publish(self, body, schema, slot):
        self.guard()
        return self.owner.publisher.publish(self.work.address, slot, body, schema, self.guard)

    def protect(self, reference, slot):
        reservation = ReserveArtifact.model_validate({"artifact": reference, "intent": {
            "runtime_owner": self.owner.artifacts.owner, "intent_id": self.work.address.identity,
            "semantic_completion_sha256": self.work.binding.sha256, "output_binding": slot}})
        saved = self.owner.leases.commands.transact(lambda conn: self.owner.prepare(conn, self.work, reservation))
        if saved is not None:
            validate_receipt(reservation, ReservationReceipt.model_validate_json(json.dumps(saved)))
            return
        receipt = self.owner.artifacts.reserve(reservation)
        validate_receipt(reservation, receipt)
        self.owner.leases.commands.transact(lambda conn: self.owner.save(conn, self.work, reservation, receipt))


class BindingCoordinator:
    def __init__(self, engine, catalog, artifacts, publisher):
        self.engine, self.catalog, self.artifacts, self.publisher = engine, catalog, artifacts, publisher
        self.leases = RuntimeLeases(engine)

    def changed(self, conn, params, run, kind):
        return self.leases._changed(conn, params, run, RunBudget(run["budget_limit"], run["reserved"], run["spent"]),
            uuid.uuid4().hex, {"kind": kind, "binding_intent": params["intent"]})

    def context(self, conn, params, row, scope):
        entry = self.catalog.require(scope, row["plan_sha256"])
        key = conn.execute(text("SELECT scope_key FROM runtime.graph_nodes WHERE " + RUN +
            " AND activation_id=:activation"), {**params, "activation": row["activation_id"]}).scalar_one()
        state = ScopeState.load(conn, params, entry.plan, key)
        node_row = next(item for item in state.nodes.values() if item["activation_id"] == row["activation_id"])
        binding = BindingInput.resolve(state.definition(node_row), state.environment)
        ensure(binding.sha256 == row["semantic_sha256"] and binding.values.record() == row["inputs"], "binding_source_cut_changed")
        ensure(node_row["status"] == "issued", "binding_node_not_issued")
        return entry, binding, node_row

    def check(self, conn, work):
        run = self.leases._run(conn, work.params)
        row = load(conn, work.params)
        ensure(row["status"] == "prepared" and run["status"] == "running", "binding_no_longer_active")
        ensure(row["lease_token"] == work.token, "binding_lease_lost")
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        ensure(now < row["deadline"], "binding_deadline_expired")
        ensure(now < row["lease_until"], "binding_lease_lost")
        self.context(conn, work.params, row, work.address.scope)
        conn.execute(text("UPDATE runtime.binding_intents SET lease_until=LEAST(deadline,clock_timestamp()+interval '30 seconds') "
            "WHERE " + SCOPE + " AND intent_id=:intent"), work.params)
        return run, row

    def claim(self, conn, principal, params):
        run = self.leases._run(conn, params)
        row = load(conn, params)
        if row["status"] != "prepared":
            return None
        now = conn.execute(text("SELECT clock_timestamp()")).scalar_one()
        reason = "binding_no_longer_active" if run["status"] != "running" else (
            "binding_deadline_expired" if now >= row["deadline"] else None)
        if reason:
            close(conn, params, row, run["revision"] + 1, reason)
            conn.execute(text("UPDATE runtime.graph_nodes SET status='blocked',reason_code=:reason WHERE " + RUN +
                " AND activation_id=:activation AND status='issued'"), {**params, "reason": reason, "activation": row["activation_id"]})
            self.changed(conn, params, run, "binding_aborted")
            queue_terminal(conn, params, (row["intent_id"],))
            return None
        if row["lease_until"] is not None and now < row["lease_until"]:
            return None
        try:
            entry, binding, _node = self.context(conn, params, row, principal.scope)
        except TransitionError as error:
            close(conn, params, row, run["revision"] + 1, str(error))
            conn.execute(text("UPDATE runtime.graph_nodes SET status='blocked',reason_code=:reason WHERE " + RUN +
                " AND activation_id=:activation AND status='issued'"), {**params, "reason": str(error), "activation": row["activation_id"]})
            self.changed(conn, params, run, "binding_aborted")
            queue_terminal(conn, params, (row["intent_id"],))
            return None
        token = uuid.uuid4().hex
        conn.execute(text("UPDATE runtime.binding_intents SET lease_token=:token,"
            "lease_until=LEAST(deadline,clock_timestamp()+interval '30 seconds') WHERE " + SCOPE + " AND intent_id=:intent"),
            {**params, "token": token})
        return ConversionWork(BindingAddress(principal.scope, params["run"], row["activation_id"], row["plan_sha256"]),
                              binding, entry, token)

    def prepare(self, conn, work, reservation):
        _run, row = self.check(conn, work)
        raw = reservation.model_dump(mode="json")
        existing = next((item for item in row["output_bindings"] if item["intent"]["output_binding"] ==
                         reservation.intent.output_binding), None)
        ensure(existing is None or existing == raw, "binding_reservation_conflict")
        if existing is None:
            conn.execute(text("UPDATE runtime.binding_intents SET output_bindings=CAST(:bindings AS jsonb) WHERE " + SCOPE +
                " AND intent_id=:intent"), {**work.params, "bindings": json.dumps([*row["output_bindings"], raw])})
        return conn.execute(text("SELECT receipt FROM runtime.binding_reservations WHERE " + SCOPE +
            " AND intent_id=:intent AND output_binding=:slot"),
            {**work.params, "slot": reservation.intent.output_binding}).scalar_one_or_none()

    def save(self, conn, work, reservation, receipt):
        run = self.leases._run(conn, work.params)
        row = load(conn, work.params)
        ensure(reservation.model_dump(mode="json") in row["output_bindings"], "binding_reservation_conflict")
        params = {**work.params, "slot": reservation.intent.output_binding, "receipt": receipt.model_dump_json()}
        inserted = conn.execute(text("INSERT INTO runtime.binding_reservations (tenant_id,project_id,intent_id,output_binding,receipt) "
            "VALUES (:tenant,:project,:intent,:slot,CAST(:receipt AS jsonb)) ON CONFLICT DO NOTHING RETURNING output_binding"), params).scalar_one_or_none()
        saved = conn.execute(text("SELECT receipt FROM runtime.binding_reservations WHERE " + SCOPE +
            " AND intent_id=:intent AND output_binding=:slot"), params).scalar_one()
        ensure(saved == receipt.model_dump(mode="json"), "binding_reservation_conflict")
        if inserted is not None and row["status"] != "prepared":
            self.changed(conn, work.params, run, "binding_late_reservation")
            queue_terminal(conn, work.params, (row["intent_id"],))

    def commit(self, conn, work, outputs, resources):
        run, row = self.check(conn, work)
        outputs.validate((work.binding.node.output,), work.address.scope)
        protected = {json.dumps(item["artifact"], sort_keys=True) for item in row["output_bindings"]}
        pending = [binding.value for binding in (*outputs.bindings, *work.binding.values.bindings)]
        while pending:
            value = pending.pop()
            if value.kind == "collection":
                pending.extend(value.items)
            elif value.kind == "artifact":
                ensure(json.dumps(value.artifact.model_dump(mode="json"), sort_keys=True) in protected, "binding_unprotected_output")
        for raw in row["output_bindings"]:
            request = ReserveArtifact.model_validate_json(json.dumps(raw))
            saved = conn.execute(text("SELECT receipt FROM runtime.binding_reservations WHERE " + SCOPE +
                " AND intent_id=:intent AND output_binding=:slot"),
                {**work.params, "slot": request.intent.output_binding}).scalar_one_or_none()
            ensure(saved is not None, "binding_unprotected_output")
            validate_receipt(request, ReservationReceipt.model_validate_json(json.dumps(saved)))
        _entry, _binding, node = self.context(conn, work.params, row, work.address.scope)
        ensure(conn.execute(text("SELECT clock_timestamp()<:deadline"), {"deadline": row["deadline"]}).scalar_one(),
               "binding_deadline_expired")
        close(conn, work.params, row, run["revision"] + 1, outputs=outputs, resources=resources)
        persist_node(conn, work.params, node, "succeeded", outputs=outputs)
        self.changed(conn, work.params, run, "binding_committed")
        queue_terminal(conn, work.params, (row["intent_id"],))

    def abort(self, conn, work, reason):
        run = self.leases._run(conn, work.params)
        row = load(conn, work.params)
        if row["status"] != "prepared" or row["lease_token"] != work.token:
            return
        close(conn, work.params, row, run["revision"] + 1, reason)
        conn.execute(text("UPDATE runtime.graph_nodes SET status='blocked',reason_code=:reason WHERE " + RUN +
            " AND activation_id=:activation AND status='issued'"),
            {**work.params, "activation": row["activation_id"], "reason": reason})
        self.changed(conn, work.params, run, "binding_aborted")
        queue_terminal(conn, work.params, (row["intent_id"],))

    def tick(self, principal):
        principal.require("maintain")
        params = {"tenant": principal.scope.tenant_id, "project": principal.scope.project_id}
        with self.engine.connect() as conn:
            row = conn.execute(text("SELECT run_id,intent_id FROM runtime.binding_intents WHERE " + SCOPE +
                " AND status='prepared' AND (lease_until IS NULL OR lease_until<=clock_timestamp() OR deadline<=clock_timestamp() "
                "OR EXISTS (SELECT 1 FROM runtime.runs r WHERE (r.tenant_id,r.project_id,r.run_id)="
                "(binding_intents.tenant_id,binding_intents.project_id,binding_intents.run_id) AND r.status<>'running')) "
                "ORDER BY opened_revision,intent_id LIMIT 1"), params).mappings().one_or_none()
        if row is None:
            return False
        work = self.leases.commands.transact(lambda conn: self.claim(conn, principal, {**params, "run": row["run_id"], "intent": row["intent_id"]}))
        if work is None:
            return False
        try:
            conversion = Conversion(work.binding, principal.scope, work.entry.schemas, ProtectedIO(self, work))
            outputs = conversion.run()
            self.leases.commands.transact(lambda conn: self.commit(conn, work, outputs, conversion.budget.record()))
        except TransitionError as error:
            reason = str(error)
            self.leases.commands.transact(lambda conn: self.abort(conn, work, reason))
        except ReservationUnavailable:
            return False
        finally:
            # Token comparison cannot release a successor coordinator's lease.
            with self.engine.begin() as conn:
                conn.execute(text("UPDATE runtime.binding_intents SET lease_token=NULL,lease_until=NULL WHERE " + SCOPE +
                    " AND intent_id=:intent AND lease_token=:token"), {**work.params, "token": work.token})
        return True
