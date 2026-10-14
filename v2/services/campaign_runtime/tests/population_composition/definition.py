"""Existing graph primitives own batching, iteration and local scientific dependencies."""

from math import ceil


def port(name, shape):
    return {"name": name, "value_type": shape}


def source(name):
    return {"kind": "input", "name": name}


def output(node, name="result"):
    return {"kind": "output", "node_id": node, "port": name}


def finish(value):
    return {"kind": "finish", "node_id": "finish", "outputs": [{"port": "result", "source": value}]}


def scope(inputs, shape, nodes, edges=None):
    return {"inputs": inputs, "outputs": [port("result", shape)], "nodes": nodes,
            "edges": [{"source": a, "target": b, "route": "next"} for a, b in
                      (edges if edges is not None else zip([n["node_id"] for n in nodes], [n["node_id"] for n in nodes][1:]))]}


def invoke(catalog, name, operation, bindings):
    return {"kind": "invoke", "node_id": name, "tool": catalog.bindings[operation],
            "inputs": [{"port": key, "source": value} for key, value in bindings.items()], "timeout_seconds": 60}


def document(body):
    return {"schema_version": "4", "profile": "deterministic-v3", "scope": {"tenant_id": "population", "project_id": "composition"},
            "campaign_id": "population-composition", "revision": 1, "context": [], "body": body}


def campaign(catalog, population=12, batch=8, generations=3):
    if any(type(x) is not int for x in (population, batch, generations)) or not 1 <= population <= 1000 or not 1 <= batch <= 32 or not 0 <= generations <= 100:
        raise ValueError("unsupported_composition_bounds")
    shape = catalog.shapes["state"]
    limits = {"max_items": max(batch, 2), "max_artifacts": max(batch, 2) + 2, "max_bytes": 262144, "timeout_seconds": 120}
    def tool(name, operation, value):
        return invoke(catalog, name, operation, {"parameters": value})
    def collection(count, missing):
        return {"kind": "collection", "item": shape, "max_items": count, "missing_slots": missing}
    def materialize(name, state, results):
        return {"kind": "artifact_materialize", "node_id": name, "fields": [
            {"name": "state", "mode": "references", "source": state},
            {"name": "results", "mode": "references", "source": results}],
            "output": port("result", catalog.shapes["collected"]), "limits": limits}
    def iteration(name, initial, body, count, field):
        return {"kind": "iterate", "node_id": name,
                "state": [{"name": "state", "value_type": shape, "initial": initial, "feedback_port": "result"}],
                "captures": [], "body": body, "max_iterations": count, "on_limit": "blocked",
                "until": {"kind": "compare", "left": {"source": {"kind": "result", "name": "result"},
                    "path": [field], "value_type": {"kind": "scalar", "scalar": "boolean", "unit": "1"}},
                    "operator": "eq", "right": {"kind": "boolean", "value": True}}}
    terminal = {"kind": "partial", "minimum": 0, "close": "all_terminal"}
    candidate = scope([port("candidate", shape)], shape, [
        tool("evaluate_a", "evaluate_a", source("candidate")),
        tool("prepare_b", "prepare", source("candidate")), tool("evaluate_b", "evaluate_b", output("prepare_b")),
        {"kind": "join", "node_id": "observations", "members": [
            {"member_id": name, "source": output(name), "required": True} for name in ("evaluate_a", "evaluate_b")],
            "policy": terminal, "output": port("result", collection(2, True))},
        materialize("fitness_inputs", source("candidate"), output("observations")),
        tool("assemble", "assemble", output("fitness_inputs")), finish(output("assemble"))],
        [("prepare_b", "evaluate_b"), ("evaluate_a", "observations"), ("evaluate_b", "observations"), ("observations", "fitness_inputs"),
         ("fitness_inputs", "assemble"), ("assemble", "finish")])
    batches = scope([port("state", shape)], shape, [tool("slice", "slice", source("state")),
        {"kind": "artifact_project", "node_id": "members", "source": output("slice"), "path": ["members"],
         "mode": "references", "output": port("result", collection(batch, False)), "limits": limits},
        {"kind": "scatter", "node_id": "candidates", "collection": output("members"), "item_input": "candidate",
         "captures": [], "max_members": batch, "max_parallel": min(batch, 8), "body": candidate,
         "result_port": "result", "output": port("result", collection(batch, True)), "policy": terminal},
        materialize("collection_inputs", output("slice"), output("candidates")),
        tool("collect", "collect", output("collection_inputs")), finish(output("collect"))])
    generation = scope([port("state", shape)], shape, [iteration("batches", source("state"), batches, ceil(population / batch), "slice_complete"),
        tool("select", "select", output("batches")), tool("vary", "vary", output("select")), finish(output("vary"))])
    return document(scope([port("specification", shape)], shape, [tool("seed", "seed", source("specification")),
        iteration("generations", output("seed"), generation, generations + 1, "campaign_stopped"), finish(output("generations"))]))


WIDTHS = (1, 3, 2, 1, 4, 2, 1, 2, 3, 1, 2, 1, 4, 1, 2, 3, 2, 1, 2)


def process_campaign(catalog):
    shape = catalog.shapes["state"]
    previous, nodes, edges = [source("precursor")], [], []
    for stage, width in enumerate(WIDTHS):
        current = []
        for index in range(width):
            name = f"stage_{stage}_{index}"
            nodes.append(invoke(catalog, name, "process_" + str(len(previous)), {"p" + str(i): s for i, s in enumerate(previous)}))
            edges.extend((s["node_id"], name) for s in previous if s["kind"] == "output")
            current.append(output(name))
        previous = current
    nodes.append({"kind": "finish", "node_id": "finish", "outputs": [{"port": "result", "source": previous[0]}]})
    edges.extend((s["node_id"], "finish") for s in previous)
    return document(scope([port("precursor", shape)], shape, nodes, edges))
