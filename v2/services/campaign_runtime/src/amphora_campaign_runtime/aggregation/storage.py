"""Transaction-local, append-only evidence; caller commits policy/audit/receipt together."""

from sqlalchemy import text

from ..compiler.catalog import canonical
from ..lifecycle.claims import RUN
from .snapshot import require


class AggregateCuts:
    @staticmethod
    def decide(conn, decision):
        cut = decision.cut
        AggregateCuts.persist(conn, cut)
        identity = cut.identity
        params = {"tenant": identity.scope.tenant_id, "project": identity.scope.project_id,
                  "run": identity.run_id, "activation": identity.activation_id}
        existing = conn.execute(text("SELECT decision_sha256,document FROM runtime.graph_aggregate_decisions WHERE " +
            RUN + " AND activation_id=:activation"), params).mappings().one_or_none()
        document = decision.record()
        if existing is not None:
            require(existing["decision_sha256"] == decision.sha256 and existing["document"] == document,
                    "aggregate_decision_conflict")
            return decision.sha256
        # A previously committed cut cannot acquire a different, later policy decision.
        revision = conn.execute(text("SELECT revision FROM runtime.runs WHERE " + RUN), params).scalar_one()
        require(revision == cut.observed_revision, "aggregate_stale_decision")
        conn.execute(text("INSERT INTO runtime.graph_aggregate_decisions "
            "(tenant_id,project_id,run_id,activation_id,cut_sha256,decision_sha256,document) "
            "VALUES (:tenant,:project,:run,:activation,:cut,:sha,CAST(:document AS jsonb))"),
            {**params, "cut": cut.sha256, "sha": decision.sha256, "document": canonical(document).decode()})
        return decision.sha256

    @staticmethod
    def persist(conn, cut):
        identity = cut.identity
        params = {"tenant": identity.scope.tenant_id, "project": identity.scope.project_id,
                  "run": identity.run_id, "activation": identity.activation_id}
        run = conn.execute(text("SELECT status,revision FROM runtime.runs WHERE " + RUN +
                                " FOR UPDATE"), params).mappings().one_or_none()
        require(run is not None, "run_unavailable")
        existing = conn.execute(text("SELECT cut_sha256,document FROM runtime.graph_aggregate_cuts WHERE " + RUN +
            " AND activation_id=:activation"), params).mappings().one_or_none()
        document = cut.record()
        if existing is not None:
            require(existing["cut_sha256"] == cut.sha256 and existing["document"] == document,
                    "aggregate_already_closed")
            return cut.sha256
        require(run["status"] == "running", "run_not_running")
        require(run["revision"] == cut.observed_revision and cut.closure_revision == cut.observed_revision + 1,
                "aggregate_stale_cut")
        kind = conn.execute(text("SELECT kind FROM runtime.graph_nodes WHERE " + RUN +
                                " AND activation_id=:activation"), params).scalar_one_or_none()
        require(kind in {"join", "scatter"}, "aggregate_node_unavailable")
        conn.execute(text("INSERT INTO runtime.graph_aggregate_cuts "
            "(tenant_id,project_id,run_id,activation_id,observed_revision,closure_revision,cut_sha256,document) "
            "VALUES (:tenant,:project,:run,:activation,:observed,:closure,:sha,CAST(:document AS jsonb))"),
            {**params, "observed": cut.observed_revision, "closure": cut.closure_revision,
             "sha": cut.sha256, "document": canonical(document).decode()})
        return cut.sha256
