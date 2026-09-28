"""Abandon old provisional uploads and retire immutable attempt keys safely."""

from sqlalchemy import text

from ..publication.uploads import SCOPE


class Cleanup:
    def __init__(self, uploads, storage, *, grace_seconds=86400):
        if not 1 <= grace_seconds <= 31536000:
            raise ValueError("Bounded positive cleanup grace required")
        self.uploads, self.storage, self.grace = uploads, storage, grace_seconds

    def sweep(self, principal, *, limit=20, after=""):
        principal.require("cleanup")
        if not 1 <= limit <= 100:
            raise ValueError("Cleanup batch must be 1..100")
        def abandon(conn):
            self.uploads._capacity(conn, principal)
            rows = conn.execute(text("SELECT upload_id,generation,expected_descriptor,status FROM artifacts.uploads u "
                "WHERE " + SCOPE + " AND actor_id=:actor AND upload_id>:after "
                "AND (status='abandoned' OR (status='provisional' AND created_at < "
                "clock_timestamp()-make_interval(secs => :grace) AND NOT EXISTS "
                "(SELECT 1 FROM artifacts.upload_attempts a WHERE a.tenant_id=u.tenant_id "
                "AND a.project_id=u.project_id AND a.upload_id=u.upload_id AND a.expires_at>clock_timestamp()))) "
                "ORDER BY upload_id LIMIT :limit FOR UPDATE"),
                {**principal.bindings, "after": after, "grace": self.grace, "limit": limit}).mappings().all()
            for row in rows:
                if row["status"] == "provisional":
                    conn.execute(text("UPDATE artifacts.uploads SET status='abandoned',selected_attempt=NULL "
                        "WHERE " + SCOPE + " AND upload_id=:upload"), {**principal.bindings, "upload": row["upload_id"]})
                    if row["generation"] == 0:
                        conn.execute(text("UPDATE artifacts.capacity SET charged_bytes=charged_bytes-:refund WHERE " + SCOPE),
                            {**principal.bindings, "refund": row["expected_descriptor"]["size_bytes"]})
            return [row["upload_id"] for row in rows]
        uploads = self.uploads.commands.transact(abandon)
        cleaned, busy = 0, 0
        for upload_id in uploads:
            with self.uploads.commands.engine.connect() as conn:
                attempts = conn.execute(text("SELECT attempt_id,storage_key FROM artifacts.upload_attempts WHERE " +
                    SCOPE + " AND upload_id=:upload AND status<>'cleaned' ORDER BY generation LIMIT :limit"),
                    {**principal.bindings, "upload": upload_id, "limit": self.uploads.limits.attempts}).mappings().all()
            for attempt in attempts:
                try:
                    with self.storage.guard(attempt["storage_key"]):
                        self._retire(principal, upload_id, attempt)
                        cleaned += 1
                except OSError:
                    # Busy writer or filesystem uncertainty: keep all bytes charged.
                    busy += 1
        return {"cleaned": cleaned, "deferred": busy, "next_cursor": uploads[-1] if len(uploads) == limit else ""}

    def _retire(self, principal, upload_id, attempt):
        params = {**principal.bindings, "upload": upload_id, "attempt": attempt["attempt_id"]}
        where = SCOPE + " AND upload_id=:upload AND attempt_id=:attempt"
        def claim(conn):
            self.uploads._capacity(conn, principal)
            upload = self.uploads._upload(conn, principal, upload_id)
            if upload["status"] != "abandoned":
                raise ValueError("Cleanup requires abandoned upload")
            row = conn.execute(text("SELECT * FROM artifacts.upload_attempts WHERE " + where + " FOR UPDATE"), params).mappings().one()
            if row["status"] == "cleaned":
                return False
            if row["status"] == "streaming":
                conn.execute(text("UPDATE artifacts.capacity SET active_streams=active_streams-1 WHERE " + SCOPE), params)
            conn.execute(text("UPDATE artifacts.upload_attempts SET status='cleaning' WHERE " + where), params)
            return True
        if not self.uploads.commands.transact(claim):
            return
        self.storage.retire(attempt["storage_key"])
        def settle(conn):
            self.uploads._capacity(conn, principal)
            row = conn.execute(text("SELECT * FROM artifacts.upload_attempts WHERE " + where + " FOR UPDATE"), params).mappings().one()
            if row["status"] == "cleaned":
                return
            refund = row["actual_bytes"] if row["actual_bytes"] is not None else row["allocated_bytes"]
            conn.execute(text("UPDATE artifacts.capacity SET charged_bytes=charged_bytes-:refund WHERE " + SCOPE),
                         {**params, "refund": refund})
            conn.execute(text("UPDATE artifacts.upload_attempts SET status='cleaned' WHERE " + where), params)
        self.uploads.commands.transact(settle)
