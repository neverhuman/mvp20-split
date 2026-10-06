"""Research-owned public process handoff; no peer-private imports or SQL."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import uuid
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).absolute().parents[5]
GRAPH = load(
    "candidate_graph_hosts",
    ROOT / "services/campaign_runtime/tests/scheduling/acceptance/probe.py",
)
HTTP = GRAPH.HTTP
KINDS = ("numeric", "polymer", "sequence")


class CandidateEnvironment(GRAPH.GraphEnvironment):
    def cli(self, kind, action, *arguments, body=None):
        result = subprocess.run(
            [
                self.config[kind],
                "-I",
                "-m",
                "amphora_" + kind + "_space",
                action,
                *arguments,
            ],
            input=body,
            cwd=self.root,
            env=HTTP.isolated_env(),
            capture_output=True,
            check=False,
            timeout=30,
        )
        assert result.returncode == 0, (kind, action, result.stderr.decode()[-1000:])
        return result.stdout

    def setup(self):
        self.scope["tenant_id"] = "candidate-handoff"
        self.tokens["research"] = uuid.uuid4().hex
        self.descriptors, self.semantic, self.inputs = {}, {}, {}
        releases, schemas, profiles = [], {}, []
        for kind in KINDS:
            descriptor = json.loads(
                self.cli(kind, "describe", "--image-sha256", "c" * 64)
            )
            self.descriptors[kind] = descriptor
            self.semantic[kind] = json.loads(self.cli(kind, "profiles"))
            filename = kind + "-descriptor.json"
            (self.root / filename).write_text(json.dumps(descriptor), encoding="utf-8")
            releases.append(
                {
                    "descriptor": filename,
                    "lock": GRAPH.BASE.WIRE.release_lock(descriptor),
                }
            )
            for direction, ports in (("input", "inputs"), ("output", "outputs")):
                raw = self.cli(kind, "schema", "--direction", direction)
                reference = descriptor["tool"][ports][0]["schema_ref"]
                assert hashlib.sha256(raw).hexdigest() == reference["sha256"]
                key = json.dumps(reference, sort_keys=True)
                if key in schemas:
                    assert (self.root / schemas[key]["path"]).read_bytes() == raw
                    continue
                filename = kind + "-" + direction + ".json"
                (self.root / filename).write_bytes(raw)
                schemas[key] = {"schema_ref": reference, "path": filename}
                profiles.append(
                    {
                        **reference,
                        "media_type": "application/json",
                        "schema_path": filename,
                    }
                )
        cases = json.loads(
            (ROOT / "contracts/fixtures/v2/executable_cases.json").read_bytes()
        )
        template = next(
            case["payload"]
            for case in cases
            if case["valid"] and case["model"] == "campaigns.definition"
        )
        graphs = []
        for kind in KINDS:
            graph = copy.deepcopy(template)
            graph.update(scope=self.scope, campaign_id="candidate-" + kind)
            graph["body"]["nodes"][0]["node_id"] = "move"
            graph["body"]["nodes"][1]["outputs"][0]["source"]["node_id"] = "move"
            graph["body"]["edges"][0]["source"] = "move"
            graph["body"]["nodes"][0]["tool"] = self.descriptors[kind]["tool"][
                "binding"
            ]
            for direction in ("inputs", "outputs"):
                port = self.descriptors[kind]["tool"][direction][0]
                graph["body"][direction][0]["value_type"] = {
                    "kind": "artifact",
                    "media_type": "application/json",
                    **{
                        key: port[key]
                        for key in ("schema_ref", "representation", "unit")
                    },
                }
            filename = kind + "-graph.json"
            (self.root / filename).write_text(json.dumps(graph), encoding="utf-8")
            graphs.append(
                {
                    "definition": filename,
                    "releases": releases,
                    "schemas": list(schemas.values()),
                }
            )
        port = HTTP.free_port()
        (self.root / "storage").mkdir()
        self.artifact_config = {
            "database_url_env": "DATABASE_URL",
            "storage_root": str(self.root / "storage"),
            "profiles": profiles,
            "principals": [
                self.principal("worker1", ["upload", "finalize", "read"]),
                self.principal("runtime", ["read", "retention"]),
                self.principal("research", ["read"]),
            ],
            "runtime": {
                "owner": "runtime",
                "endpoint": f"http://127.0.0.1:{port}/v1/completion-intents/outcome",
                "token_env": "TOKEN_ARTIFACT",
            },
        }
        (self.root / "artifact-original.json").write_text(
            json.dumps(self.artifact_config), encoding="utf-8"
        )
        self.artifact = self.host(
            "artifact",
            "amphora_data_artifacts",
            self.artifact_config,
            "AMPHORA_ARTIFACT_DATABASE_URL",
        )
        self.runtime = self.host(
            "runtime",
            "amphora_campaign_runtime",
            {
                "database_url_env": "DATABASE_URL",
                "fixtures": [],
                "graphs": graphs,
                "tools": [item["tool"] for item in self.descriptors.values()],
                "principals": [
                    self.principal(
                        "admin",
                        [
                            "admit",
                            "cancel",
                            "read",
                            "inspect_receipts",
                            "deliver",
                            "maintain",
                        ],
                    ),
                    self.principal("artifact", ["outcome"]),
                    self.principal("worker1", ["claim", "renew", "complete", "read"]),
                ],
                "artifacts": {
                    "runtime_owner": "runtime",
                    "reserve_endpoint": self.artifact.endpoint + "/v1/reservations",
                    "token_env": "TOKEN_RUNTIME",
                },
                "inspection": {"cursor_key_env": "CURSOR_KEY"},
            },
            "AMPHORA_RUNTIME_DATABASE_URL",
            port,
        )
        self.runtime_relay = HTTP.FaultRelay(self.runtime.endpoint)
        self.resources.append(self.runtime_relay)
        self.plans = self.compile(self.config["runtime"])
        config = {
            "database_url_env": "DATABASE_URL",
            "principals": [
                self.principal("admin", ["declare_candidate", "read_candidate"])
            ],
            "candidates": {
                "data": {
                    "endpoint": self.artifact.endpoint,
                    "token_env": "TOKEN_RESEARCH",
                },
                "profiles": [
                    {
                        "schema": self.descriptors[kind]["tool"]["outputs"][0][
                            "schema_ref"
                        ],
                        "kind": kind,
                        "semantic_profile": self.semantic[kind]["profile"],
                    }
                    for kind in KINDS
                ],
            },
        }
        path = self.root / "research.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        env = dict(
            HTTP.isolated_env(),
            DATABASE_URL=os.environ["AMPHORA_RESEARCH_DATABASE_URL"],
            TOKEN_ADMIN=self.tokens["admin"],
            TOKEN_RESEARCH=self.tokens["research"],
        )
        self.research = HTTP.Service(
            self.config["research"],
            "amphora_research",
            path,
            env,
            self.root,
            HTTP.free_port(),
        )
        self.resources.append(self.research)
        self.research.ready(self.tokens["admin"], "/health")

    def publish_input(self, kind):
        data = json.loads(Path(__file__).with_name(kind + "-request.json").read_bytes())
        data["source"].update(scope=self.scope, profile=self.semantic[kind]["profile"])
        data["operator"] = self.semantic[kind]["operator"]
        body = json.dumps(data).encode()
        content = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body),
            "media_type": "application/json",
            "schema_ref": self.descriptors[kind]["tool"]["inputs"][0]["schema_ref"],
        }
        token = self.tokens["worker1"]
        upload = HTTP.decoded(
            self.artifact.endpoint,
            "/v1/uploads",
            token,
            self.command("artifacts.begin_upload", {"content": content}, "worker1"),
        )
        assert (
            HTTP.request(
                self.artifact.endpoint,
                "/v1/uploads/" + upload["upload_id"] + "/content",
                token,
                body,
                "PUT",
            )[0]
            == 200
        )
        return HTTP.decoded(
            self.artifact.endpoint,
            "/v1/artifacts/finalize",
            token,
            self.command(
                "artifacts.finalize",
                {"upload_id": upload["upload_id"], "content": content},
                "worker1",
            ),
        )["artifact"]
