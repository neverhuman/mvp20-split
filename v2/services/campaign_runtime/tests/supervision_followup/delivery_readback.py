"""Runtime-owned read-only delivery classification for the two acceptance runs."""

import json
import os
import sys

from sqlalchemy import create_engine, text


def main():
    engine=create_engine(os.environ['PROOF_DATABASE_URL'],connect_args={'options':'-c statement_timeout=5000'})
    try:
        with engine.connect() as conn:
            assert conn.execute(text('SELECT current_user')).scalar_one()=='runtime_service'
            rows=conn.execute(text('SELECT a.run_id,o.target,o.status,count(*) AS count FROM runtime.outbox o '
                'JOIN runtime.audit_events a USING(event_id) WHERE a.run_id IN (:original,:successor) '
                'GROUP BY a.run_id,o.target,o.status ORDER BY a.run_id,o.target,o.status'),
                {'original':sys.argv[1],'successor':sys.argv[2]}).mappings().all()
            print(json.dumps([dict(row) for row in rows]))
    finally:
        engine.dispose()


if __name__=='__main__':
    main()
