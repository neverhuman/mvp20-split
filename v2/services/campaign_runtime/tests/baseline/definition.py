"""Authored solver orchestration; tools perform one stage, graph owns all repetition."""


def campaign(scope, releases, generations, *, continuation=False):
    if type(generations) is not int or not 0 <= generations <= 8:
        raise ValueError("unsupported_fixture_generation_count")
    tools = {name: descriptor["tool"] for name, descriptor in releases.items()}
    limits = {"max_items": 8, "max_artifacts": 16, "max_bytes": 262144, "timeout_seconds": 120}

    def shape(stage, direction):
        port = tools[stage][direction][0]
        return {"kind": "artifact", "media_type": "application/json",
                **{key: port[key] for key in ("schema_ref", "representation", "unit")}}

    def port(name, value_type):
        return {"name": name, "value_type": value_type}

    def output(name, name_of_port="result"):
        return {"kind": "output", "node_id": name, "port": name_of_port}

    def finish(source, name="result"):
        return {"kind": "finish", "node_id": "finish", "outputs": [{"port": name, "source": source}]}

    def body(inputs, outputs, nodes):
        return {"inputs": inputs, "outputs": outputs, "nodes": nodes,
                "edges": [{"source": a["node_id"], "target": b["node_id"], "route": "next"}
                          for a, b in zip(nodes, nodes[1:], strict=False)]}

    def invoke(name, stage, source):
        return {"kind": "invoke", "node_id": name, "tool": tools[stage]["binding"],
                "inputs": [{"port": "parameters", "source": source}], "timeout_seconds": 60}

    requests = {"kind": "collection", "item": shape("score", "inputs"), "max_items": 8, "missing_slots": False}
    results = {"kind": "collection", "item": shape("score", "outputs"), "max_items": 8, "missing_slots": True}
    state_shape = shape("retain", "outputs")

    def score_batch(batch):
        project = {"kind": "artifact_project", "node_id": "proposals", "source": batch, "path": ["candidates"],
                   "mode": "items", "output": port("result", requests), "limits": limits}
        scatter = {"kind": "scatter", "node_id": "score_batch", "collection": output("proposals"),
            "item_input": "candidate", "captures": [], "max_members": 8, "max_parallel": 8,
            "body": body([port("candidate", shape("score", "inputs"))], [port("result", shape("score", "outputs"))],
                [invoke("score", "score", {"kind": "input", "name": "candidate"}), finish(output("score"))]),
            "result_port": "result", "output": port("result", results),
            "policy": {"kind": "partial", "minimum": 0, "close": "all_terminal"}}
        collect = {"kind": "artifact_materialize", "node_id": "collect", "fields": [
            {"name": "batch", "mode": "inline", "source": batch},
            {"name": "results", "mode": "inline", "source": output("score_batch")}],
            "output": port("result", shape("retain", "inputs")), "limits": limits}
        return [project, scatter, collect, invoke("retain", "retain", output("collect"))]

    nodes = [] if continuation else [invoke("seed", "seed", {"kind": "input", "name": "parameters"}), *score_batch(output("seed"))]
    initial = {"kind": "input", "name": "parameters"} if continuation else output("retain")
    final = initial
    if generations:
        loop_body = body([port("state", state_shape)], [port("state", state_shape)], [
            invoke("select", "select", {"kind": "input", "name": "state"}),
            invoke("mutate", "mutate", output("select")), *score_batch(output("mutate")), finish(output("retain"), "state")])
        nodes.append({"kind": "iterate", "node_id": "generations", "state": [{"name": "state", "value_type": state_shape,
            "initial": initial, "feedback_port": "state"}], "captures": [], "body": loop_body,
            "until": {"kind": "constant", "value": False}, "max_iterations": generations, "on_limit": "finish"})
        final = output("generations", "state")
    nodes.append(finish(final))
    return {"schema_version": "4", "profile": "deterministic-v3", "scope": scope, "campaign_id": "source-solver-fixture",
            "revision": 1, "context": [], "body": body([port("parameters", state_shape if continuation else shape("seed", "inputs"))],
                [port("result", state_shape)], nodes)}
