"""Test-only barriers around the production host/store; excluded from wheels."""

import argparse
import json
import sys
from pathlib import Path

import uvicorn
from amphora_knowledge.rebuild.store import RebuildStore
from amphora_knowledge.transport.host import KnowledgeHost
from sqlalchemy import event

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--port", required=True, type=int)
parser.add_argument("--barrier", required=True, choices=["candidate_staged", "publication_before_result", "publication_committed"])
args = parser.parse_args()
reached = False


def barrier():
    global reached
    if not reached:
        reached = True
        print(json.dumps({"barrier": args.barrier}), flush=True)
        if not sys.stdin.readline():
            raise RuntimeError("test_barrier_closed")


host = KnowledgeHost.configured(json.loads(Path(args.config).read_text(encoding="utf-8")))
if args.barrier == "candidate_staged":
    original = RebuildStore.stage

    def staged(self, candidate):
        original(self, candidate)
        barrier()

    RebuildStore.stage = staged
elif args.barrier == "publication_committed":
    original = RebuildStore.publish

    def published(self, candidate):
        result = original(self, candidate)
        if result is not None:
            barrier()
        return result

    RebuildStore.publish = published
else:
    def before_result(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO knowledge.rebuild_results"):
            barrier()

    event.listen(host.engine, "before_cursor_execute", before_result)
try:
    uvicorn.run(host.app, host="127.0.0.1", port=args.port, access_log=False)
finally:
    host.close()
