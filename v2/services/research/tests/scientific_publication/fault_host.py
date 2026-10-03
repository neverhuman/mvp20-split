"""Scientific Artifact publisher test host; process barriers are excluded from wheels."""
import argparse
import json
import sys
from pathlib import Path

import uvicorn
from amphora_research.scientific_publication.store import ScientificPublicationStore
from amphora_research.transport.host import ResearchHost
from amphora_tool_protocol import ArtifactClient
from sqlalchemy import event

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--port", required=True, type=int)
parser.add_argument("--barrier", required=True)
args = parser.parse_args()
reached = False


def barrier():
    global reached
    if not reached:
        reached = True
        print(json.dumps({"barrier":args.barrier}), flush=True)
        if not sys.stdin.readline():
            raise RuntimeError("test_barrier_closed")


acquire, renew = ScientificPublicationStore.acquire, ScientificPublicationStore.renew


def short_acquire(self, initial, seconds=60):
    return acquire(self, initial, seconds=5)


def short_renew(self, lease, seconds=60):
    return renew(self, lease, seconds=5)


ScientificPublicationStore.acquire, ScientificPublicationStore.renew = short_acquire, short_renew
host = ResearchHost.configured(json.loads(Path(args.config).read_text(encoding="utf-8")))
if args.barrier == "prepared":
    original = ScientificPublicationStore.begin

    def begin(self, *values):
        result = original(self, *values)
        barrier()
        return result

    ScientificPublicationStore.begin = begin
elif args.barrier in {"begin_returned", "stream_returned", "data_finalized"}:
    method = {"begin_returned":"begin_derived", "stream_returned":"stream", "data_finalized":"finalize"}[args.barrier]
    original = getattr(ArtifactClient, method)

    def returned(self, *values, **kwargs):
        result = original(self, *values, **kwargs)
        barrier()
        return result

    setattr(ArtifactClient, method, returned)
elif args.barrier in {"stream_started", "stream_verified", "finalizing", "terminal_committed"}:
    action = {"stream_started":"streaming", "stream_verified":"streamed", "finalizing":"finalizing",
              "terminal_committed":"published"}[args.barrier]
    original = ScientificPublicationStore.advance

    def advance(self, lease, position, transition, data=None):
        result = original(self, lease, position, transition, data)
        if transition == action:
            barrier()
        return result

    ScientificPublicationStore.advance = advance
elif args.barrier == "terminal_before_commit":
    def before_commit(_connection, _cursor, statement, params, _context, _many):
        if statement.startswith("INSERT INTO research.science_publication_events") and json.loads(params["body"])["action"] == "published":
            barrier()

    event.listen(host.engine, "after_cursor_execute", before_commit)
else:
    raise AssertionError("unknown scientific publication barrier")
try:
    uvicorn.run(host.app, host="127.0.0.1", port=args.port, access_log=False)
finally:
    host.close()
