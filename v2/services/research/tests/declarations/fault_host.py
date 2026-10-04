"""Test-only registration barriers around the production transaction boundary."""
import argparse
import json
import sys
from pathlib import Path

import uvicorn
from amphora_research.declarations.registration import DeclarationRegistrar
from amphora_research.transport.host import ResearchHost
from sqlalchemy import event

parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--port", required=True, type=int)
parser.add_argument("--barrier", required=True, choices=["before_commit", "after_commit"])
args = parser.parse_args()


def barrier():
    print(json.dumps({"barrier": args.barrier}), flush=True)
    if not sys.stdin.readline():
        raise RuntimeError("test_barrier_closed")


host = ResearchHost.configured(json.loads(Path(args.config).read_text(encoding="utf-8")))
if args.barrier == "before_commit":
    def pause(_connection, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO research.declaration_registrations"):
            barrier()
    event.listen(host.engine, "after_cursor_execute", pause)
else:
    original = DeclarationRegistrar.register
    def register(self, *args):
        result = original(self, *args)
        barrier()
        return result
    DeclarationRegistrar.register = register
try:
    uvicorn.run(host.app, host="127.0.0.1", port=args.port, access_log=False)
finally:
    host.close()
