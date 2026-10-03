"""Test-only barriers around real owner commits; excluded from Research wheels."""
import argparse
import json
import sys
from pathlib import Path

import uvicorn
from amphora_research.observations.intake_store import LabIntakeStore
from amphora_research.observations.interpretation.store import InterpretationStore
from amphora_research.transport.host import ResearchHost
from sqlalchemy import event

parser = argparse.ArgumentParser()
parser.add_argument("--config",required=True)
parser.add_argument("--port",required=True,type=int)
parser.add_argument("--barrier",required=True)
args = parser.parse_args()
family,stage = args.barrier.split(":")
assert family in {"lab","interpretation"}
assert stage in {"intent_committed","result_before_commit","result_committed"}
reached = False


def barrier():
    global reached
    if not reached:
        reached = True
        print(json.dumps({"barrier":args.barrier}),flush=True)
        if not sys.stdin.readline():
            raise RuntimeError("test_barrier_closed")


host = ResearchHost.configured(json.loads(Path(args.config).read_text()))
owner = LabIntakeStore if family == "lab" else InterpretationStore
if stage == "result_before_commit":
    table = "lab_observations" if family == "lab" else "interpretation_experiments"

    def before_commit(_connection, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO research."+table+" "):
            barrier()

    event.listen(host.engine,"after_cursor_execute",before_commit)
else:
    method = "begin" if stage == "intent_committed" else "complete"
    original = getattr(owner,method)

    def committed(self, *values, **kwargs):
        result = original(self,*values,**kwargs)
        barrier()
        return result

    setattr(owner,method,committed)
try:
    uvicorn.run(host.app,host="127.0.0.1",port=args.port,access_log=False)
finally:
    host.close()
