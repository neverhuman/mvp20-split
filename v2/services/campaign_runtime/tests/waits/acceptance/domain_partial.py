"""Public proof that explicit partial collection preserves progress and missing evidence."""
import copy
import json
from urllib.parse import urlencode

from amphora_tool_protocol import HttpTransport


def prove_partial(runtime, root, corrected):
    receipt = corrected["record"]["receipt"]
    report = root["record"]["receipt"]["outcome"]["output"]
    assert receipt["outcome"]["status"] == "abstained"

    def configure(definition, inputs):
        body = definition["body"]
        wait, finish = body["nodes"]
        wait["expected_revision"] = receipt["revision"]
        waits = [dict(copy.deepcopy(wait), node_id=name) for name in ("uncertain-a", "uncertain-b")]
        item_type = wait["output"]["value_type"]
        body["inputs"].append({"name":"prior-report", "value_type":item_type})
        inputs.append({"port":"prior-report", "value":report})
        shape = {"kind":"collection", "item":item_type, "max_items":3, "missing_slots":True}
        body["outputs"] = [{"name":"results", "value_type":shape}]
        members = [{"member_id":"prior-report", "source":{"kind":"input", "name":"prior-report"}}]
        members += [{"member_id":node["node_id"], "source":{"kind":"output", "node_id":node["node_id"],
                    "port":"result"}, "required":False} for node in waits]
        join = {"kind":"join", "node_id":"progress", "members":members,
                "policy":{"kind":"partial", "minimum":1, "close":"all_terminal"},
                "output":{"name":"results", "value_type":shape}}
        finish["outputs"] = [{"port":"results", "source":{"kind":"output", "node_id":"progress", "port":"results"}}]
        body["nodes"] = waits + [join, finish]
        body["edges"] = [{"source":node["node_id"], "target":"progress", "route":"next"} for node in waits]
        body["edges"].append({"source":"progress", "target":"finish", "route":"next"})

    admission, page = runtime.open_graph("assessment-partial", root, configure)
    closures = []
    for node in page["nodes"]:
        if node["kind"] != "await":
            continue
        path = "/v1/graph-runs/" + runtime.run + "/waits/" + node["activation_id"]
        opened = runtime.runtime.request(path)
        assert opened["closure"] is None
        expected = opened["expectation"]
        command = runtime.command("graph.submit_receipt", {"run_id":runtime.run,
            "activation_id":node["activation_id"], "wait_revision":expected["wait_revision"],
            "expectation_sha256":opened["expectation_sha256"], "receipt":receipt}, actor=receipt["issuer_id"])
        response = HttpTransport(runtime.endpoint,"j"*32).request("POST","/v1/graph-receipts",json.dumps(command).encode())
        assert response.status == 200
        accepted = json.loads(response.body)
        assert accepted["outcome"]["status"] == "accepted", accepted
        closed = runtime.runtime.request(path)
        assert closed["closure"]["outcome"]["status"] == "abstained"
        assert closed["closure"]["outcome"]["receipt"] == receipt
        closures.append(closed)
    assert len(closures) == 2
    runtime.runtime.request("/v1/graph-runs/advance", runtime.command("graph.advance",{"run_id":runtime.run}))
    graph = runtime.runtime.request("/v2/graph-runs/" + runtime.run)
    assert graph["status"] == "completed" and graph["spent"] == graph["reserved"] == 0, graph
    join = next(node for node in graph["nodes"] if node["kind"] == "join")
    base = "/v1/graph-observations/" + runtime.run + "/nodes"
    snapshot = runtime.runtime.request(base)
    values = runtime.runtime.request(base + "/" + join["activation_id"] + "/outputs/results?" +
        urlencode({"snapshot_token":snapshot["snapshot"]["snapshot_token"]}))
    items = [item["value"] for item in values["items"]]
    assert len(items) == 3 and values["next_cursor"] is None, values
    assert [item for item in items if item["kind"] == "artifact"] == [report]
    missing = [item for item in items if item["kind"] == "missing"]
    assert {item["member_id"] for item in missing} == {"uncertain-a","uncertain-b"}
    assert all(item["reason_code"] == receipt["outcome"]["reason_code"] for item in missing), missing
    runtime.results["partial_progress"] = {"admission":admission,"graph":graph,"closures":closures,
        "values":values,"prior_report_role":"retained_context_not_current_scientific_acceptance"}
