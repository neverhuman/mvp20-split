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
KINDS = ("numeric", "polymer", "sequence", "digest")


class ReuseEnvironment(GRAPH.GraphEnvironment):
    def cli(self, kind, action, *arguments, body=None):
        result = subprocess.run(
            [
                self.config[kind],
                "-I",
                "-m",
                ("amphora_synthetic_digest" if kind == "digest" else "amphora_" + kind + "_space"),
                action,
                *arguments,
                *([] if kind == "digest" else ["--operation", "canonicalize"]),
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
        self.scope["tenant_id"] = "reuse-handoff"
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
            graph.update(scope=self.scope, campaign_id="reuse-" + kind)
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
        raw = b'{"type":"object"}'
        (self.root / 'context-schema.json').write_bytes(raw)
        profiles.append({'schema_id':'fixture.reuse-context','version':'1','sha256':hashlib.sha256(raw).hexdigest(),
                         'media_type':'application/json','schema_path':'context-schema.json'})
        self.references = {profile['schema_id']:{key:profile[key] for key in ('schema_id','version','sha256')} for profile in profiles}
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
                    self.principal("research", ["read", "inspect_receipts"]),
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

    def publish(self, body, schema):
        content = {'sha256':hashlib.sha256(body).hexdigest(),'size_bytes':len(body),
                   'media_type':'application/json','schema_ref':self.references[schema]}
        token = self.tokens['worker1']
        upload = HTTP.decoded(self.artifact.endpoint,'/v1/uploads',token,
            self.command('artifacts.begin_upload',{'content':content},'worker1'))
        assert HTTP.request(self.artifact.endpoint,'/v1/uploads/'+upload['upload_id']+'/content',token,body,'PUT')[0] == 200
        return HTTP.decoded(self.artifact.endpoint,'/v1/artifacts/finalize',token,
            self.command('artifacts.finalize',{'upload_id':upload['upload_id'],'content':content},'worker1'))['artifact']

    def run_tool(self, kind, reference):
        port = self.descriptors[kind]['tool']['inputs'][0]
        receipt = HTTP.decoded(self.runtime.endpoint,'/v1/graph-runs',self.tokens['admin'],self.command('graph.admit',{
            'plan_sha256':self.plans['reuse-'+kind]['sha256'],
            'inputs':[{'port':'parameters','value':{'kind':'artifact','artifact':reference,
                'representation':port['representation'],'unit':'1'}}], 'budget':{'limit':4}}))
        assert receipt['outcome']['status'] == 'accepted'
        self.active_run = receipt['outcome']['committed']['object_id']
        self.advance()
        worker = {'actor_id':'worker1','scope':self.scope,'run_id':self.active_run,'image_sha256':'c'*64,
            'runtime':{'endpoint':self.runtime.endpoint,'token_env':'WORKER_TOKEN'},
            'artifacts':{'endpoint':self.artifact.endpoint,'token_env':'WORKER_TOKEN'},'lease_seconds':90}
        path = self.root / (kind+'-worker.json');path.write_text(json.dumps(worker),encoding='utf-8')
        command = [self.config[kind],'-I','-m',('amphora_synthetic_digest' if kind=='digest' else 'amphora_'+kind+'_space'),
            'worker','--config',str(path)]
        if kind!='digest':command.extend(['--operation','canonicalize'])
        result = subprocess.run(command,cwd=self.root,env=dict(HTTP.isolated_env(),WORKER_TOKEN=self.tokens['worker1']),
            capture_output=True,timeout=120)
        assert result.returncode == 0, result.stderr.decode()[-1000:]
        outcome = json.loads(result.stdout)
        assert outcome['status']=='completion_accepted' and outcome['outcome']=='succeeded', outcome
        for _ in range(8):
            graph = self.advance()
            if graph['status']=='completed':break
        assert graph['status']=='completed' and graph['spent']==1
        selected = {'scope':self.scope,'run_id':self.active_run,'completion_id':outcome['operation_id']}
        proof = HTTP.decoded(self.runtime.endpoint,'/v1/runs/'+self.active_run+'/completions/'+outcome['operation_id']+'/producer',self.tokens['research'])
        output = proof['completion']['result']['outcome']['outputs'][0]['artifact']
        value = HTTP.decoded(self.artifact.endpoint,'/v1/artifacts/'+output['artifact_id']+'/content',self.tokens['worker1'])
        self.active_run = None
        return selected,proof,output,value

    def research_host(self, body, port=None):
        path = self.root/'research.json';path.write_text(json.dumps(body),encoding='utf-8')
        env = dict(HTTP.isolated_env(),DATABASE_URL=os.environ['AMPHORA_RESEARCH_DATABASE_URL'])
        env.update({'TOKEN_'+name.upper():value for name,value in self.tokens.items()})
        host = HTTP.Service(self.config['research'],'amphora_research',path,env,self.root,port or HTTP.free_port())
        self.resources.append(host);host.ready(self.tokens['admin'],'/health')
        return host
