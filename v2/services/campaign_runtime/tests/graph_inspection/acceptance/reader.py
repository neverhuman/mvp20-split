"""Independent public-contract-only observer; receives its credential solely via environment."""

import importlib.util
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from amphora_contracts_graph_runtime import (
    GraphInvalidationPage,
    GraphNodeDetail,
    GraphSnapshotPage,
    GraphValuePage,
)


def main():
    for absent in ("amphora_campaign_runtime", "amphora_data_artifacts", "amphora_capability_registry", "sqlalchemy", "fastapi"):
        assert importlib.util.find_spec(absent) is None, absent
    job = json.loads(sys.stdin.read())
    base = job["endpoint"] + "/v1/graph-observations/" + job["run"]
    opener = build_opener(ProxyHandler({}))

    def read(path, model, **params):
        query = urlencode({key: value for key, value in params.items() if value is not None})
        request = Request(base + path + ("?" + query if query else ""), headers={"Authorization": "Bearer " + os.environ["OBSERVER_TOKEN"]})
        with opener.open(request, timeout=10) as response:
            return model.model_validate_json(response.read())

    if job["operation"] == "snapshot":
        result = read("/nodes", GraphSnapshotPage, limit=1).model_dump(mode="json")
    elif job["operation"] == "events":
        cursor, events = job["cursor"], []
        for _ in range(1000):
            page = read("/invalidations", GraphInvalidationPage, cursor=cursor, limit=2)
            duplicate = read("/invalidations", GraphInvalidationPage, cursor=cursor, limit=2)
            assert duplicate.entries == page.entries and duplicate.observed_revision == page.observed_revision
            events.extend(entry.model_dump(mode="json") for entry in page.entries)
            cursor = page.next_cursor
            if not page.has_more:
                break
        else:
            raise AssertionError("bounded_event_probe_exhausted")
        result = {"entries": events, "observed_revision": page.observed_revision}
    else:
        assert job["operation"] == "resume"
        first = GraphSnapshotPage.model_validate_json(json.dumps(job["first"]))
        nodes, cursor = list(first.nodes), first.next_cursor
        for _ in range(1000):
            if not cursor:
                break
            page = read("/nodes", GraphSnapshotPage, cursor=cursor, limit=3)
            assert page.snapshot == first.snapshot
            nodes.extend(page.nodes)
            cursor = page.next_cursor
        else:
            raise AssertionError("bounded_node_probe_exhausted")
        assert len(nodes) == first.snapshot.node_count == len({node.activation_id for node in nodes})
        details, values = [], []
        for node in nodes:
            path = "/nodes/" + node.activation_id
            detail = read(path, GraphNodeDetail, snapshot_token=first.snapshot.snapshot_token, limit=1)
            assert detail.cut == first.snapshot.cut and detail.node == node
            attempts, next_attempt = list(detail.attempts), detail.next_cursor
            while next_attempt:
                following = read(path, GraphNodeDetail, snapshot_token=first.snapshot.snapshot_token, cursor=next_attempt, limit=1)
                assert following.cut == detail.cut
                attempts.extend(following.attempts)
                next_attempt = following.next_cursor
            record = detail.model_dump(mode="json")
            record.update(attempts=[attempt.model_dump(mode="json") for attempt in attempts], next_cursor=None)
            details.append(record)
            for output in detail.outputs:
                items, next_value = [], None
                for _ in range(10001):
                    page = read(path + "/outputs/" + output.port, GraphValuePage,
                        snapshot_token=first.snapshot.snapshot_token, cursor=next_value, limit=2)
                    assert page.cut == detail.cut and page.item_count == output.item_count
                    items.extend(item.model_dump(mode="json") for item in page.items)
                    next_value = page.next_cursor
                    if not next_value:
                        break
                assert len(items) == output.item_count and [item["index"] for item in items] == list(range(output.item_count))
                values.append({"activation_id": node.activation_id, "port": output.port, "items": items})
        result = {"cut": first.snapshot.cut.model_dump(mode="json"), "nodes": [node.model_dump(mode="json") for node in nodes],
                  "details": details, "values": values}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
