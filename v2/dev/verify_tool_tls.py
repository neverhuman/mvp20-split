"""Actual Linux image SDK through the local TLS proxy; synthetic upstream only."""

import argparse
import hashlib
import http.server
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.proxy import OwnerRoute, ToolAccessServer

TOKEN = "synthetic-tls-route-token-0000000000000000"
BODY = b'{"synthetic_transport_probe":true}'


class Owner(http.server.BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        valid = (
            self.path == "/v1/commands"
            and raw == BODY
            and self.headers.get("Authorization") == "Bearer " + TOKEN
        )
        self.received.append(valid)
        self.send_response(200 if valid else 403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *_args):
        pass


def docker(*args):
    result = subprocess.run(
        ["docker", *args],
        capture_output=True,
        text=True,
        timeout=45,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError("Tool TLS container probe failed")
    return result.stdout.strip()


def verify(output, identity_directory, image, openssl):
    output.mkdir(parents=True, exist_ok=False)
    identity = TLSIdentity.create(identity_directory, "amphora-tool-tls-probe", openssl)
    image_id = docker("image", "inspect", image, "--format", "{{.Id}}")
    assert image_id.startswith("sha256:") and len(image_id) == 71
    owner = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Owner)
    proxy = ToolAccessServer(identity, OwnerRoute("runtime", owner.server_port), port=0)
    threads = [threading.Thread(target=server.serve_forever) for server in (owner, proxy)]
    for thread in threads:
        thread.start()
    cases = []
    try:
        for variant in ("trusted", "untrusted", "plain_http"):
            endpoint = (
                ("http" if variant == "plain_http" else "https")
                + "://host.docker.internal:"
                + str(proxy.server_port)
            )
            script = (
                "import json,importlib.metadata as m; "
                "from amphora_tool_protocol import HttpTransport; "
                "from amphora_tool_protocol.transport import ProtocolError;\n"
                "try:\n r=HttpTransport("
                + repr(endpoint)
                + ","
                + repr(TOKEN)
                + ').request("POST","/v1/commands",'
                + repr(BODY)
                + '); result={"status":r.status,"body_matches":r.body=='
                + repr(BODY)
                + "}\n"
                'except ProtocolError as error: result={"rejected":str(error)}\n'
                'result["sdk_version"]=m.version("amphora-tool-protocol"); '
                'result["tool_version"]=m.version("amphora-evolution-search"); print(json.dumps(result))'
            )
            command = [
                "run",
                "--rm",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--mount",
                "type=bind,src=" + str(identity.certificate) + ",dst=/run/amphora-cert.pem,readonly",
            ]
            if variant == "trusted":
                command += ["--env", "SSL_CERT_FILE=/run/amphora-cert.pem"]
            result = json.loads(docker(*command, "--entrypoint", "python", image_id, "-c", script))
            assert result["sdk_version"] == "0.2.0"
            if variant == "trusted":
                assert result.get("status") == 200 and result["body_matches"]
            if variant == "untrusted":
                assert result.get("rejected") == "transport_lost"
            if variant == "plain_http":
                assert result.get("rejected") == "invalid_service_endpoint"
            cases.append({"variant": variant, **result})
        assert Owner.received == [True]
    finally:
        for server in (proxy, owner):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(6)
            assert not thread.is_alive()
    record = {
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "passed",
        "image_id": image_id,
        "certificate_sha256": identity.certificate_sha256,
        "payload_sha256": hashlib.sha256(BODY).hexdigest(),
        "cases": cases,
        "scope": "Actual Linux image/SDK and host TLS proxy; synthetic upstream, not actual Runtime or scientific execution",
        "limits": [
            "No global Docker settings or system trust changed",
            "Only public certificate mounted in container",
            "No insecure TLS bypass or SDK change",
            "Encrypted private key and DPAPI password retained locally",
        ],
    }
    (output / "evidence.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"status": "passed", "variants": len(cases), "tool_version": cases[0]["tool_version"]}),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--identity-directory", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--openssl", type=Path, required=True)
    args = parser.parse_args()
    verify(args.output.absolute(), args.identity_directory.absolute(), args.image, args.openssl.absolute())
