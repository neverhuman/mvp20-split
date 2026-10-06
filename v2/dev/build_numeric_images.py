"""Build two offline numeric/evaluator images and verify explicit capability profiles."""

import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from build_tool_images import closure
from check_boundaries import ROOT, project_specs
from numeric_image_golden import verify_golden


class ImageBuild:
    def __init__(self, output):
        self.output = output.absolute()
        self.output.mkdir(parents=True, exist_ok=False)
        self.log = self.output / "build.log"

    def run(self, command, payload=None):
        result = subprocess.run([str(item) for item in command], input=payload, capture_output=True,
                                check=False, timeout=600)
        with self.log.open("ab") as stream:
            stream.write(result.stdout + result.stderr)
        if result.returncode:
            raise RuntimeError("Image operation failed; inspect " + str(self.log))
        return result.stdout

    def build(self, base):
        if "@sha256:" not in base:
            raise ValueError("Digest-pinned Python 3.12 base required")
        uv = ROOT / ".venv/Scripts/uv.exe"
        specs = {config["project"]["name"]: (path, config, module) for path, config, module in project_specs()}
        names = ("amphora-evolution-search", "amphora-synthetic-objectives")
        wheels = self.output / "built-wheels"
        for name in sorted(set.union(*(closure(name, specs) for name in names))):
            self.run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
        manifest = {"profile": "numeric-search-images-v1", "created_at": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    "base": base, "platform": "linux/amd64", "tools": []}
        for name in names:
            project, _config, module = specs[name]
            context = self.output / name
            context.mkdir()
            self.run([uv, "export", "--project", project, "--locked", "--no-dev", "--no-emit-local", "--output-file", context / "requirements.txt"])
            local = context / "local"
            local.mkdir()
            hashes = {}
            for dependency in sorted(closure(name, specs)):
                wheel = next(wheels.glob(dependency.replace("-", "_") + "-*.whl"))
                shutil.copy2(wheel, local / wheel.name)
                hashes[wheel.name] = hashlib.sha256(wheel.read_bytes()).hexdigest()
            download = context / "Download.Dockerfile"
            download.write_text(f"FROM {base}\nCOPY requirements.txt /requirements.txt\n"
                "RUN python -m pip download --require-hashes --only-binary=:all: --dest /resolved -r /requirements.txt\n"
                "COPY local /resolved\n", encoding="utf-8")
            tag = "amphora/" + name.removeprefix("amphora-") + ":bp08-" + uuid.uuid4().hex[:12]
            self.run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
                      "-f", download, "-t", tag + "-dependencies", context])
            container = self.run(["docker", "create", tag + "-dependencies"]).decode().strip()
            try:
                self.run(["docker", "cp", container + ":/resolved", context / "wheels"])
            finally:
                self.run(["docker", "rm", container])
            final = context / "image"
            final.mkdir()
            shutil.copytree(context / "wheels", final / "wheels")
            shutil.copy2(project / "Dockerfile", final / "Dockerfile")
            metadata = context / "image-metadata.json"
            self.run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
                      "--build-arg", "PYTHON_BASE=" + base, "--metadata-file", metadata, "-t", tag, final])
            built = json.loads(metadata.read_bytes())
            digest = built["containerimage.digest"]
            inspected = json.loads(self.run(["docker", "image", "inspect", tag]))[0]
            assert digest == inspected.get("Descriptor", {}).get("digest") or any(
                item.endswith("@" + digest) for item in inspected.get("RepoDigests", []))
            assert inspected["Architecture"] == "amd64" and inspected["Os"] == "linux"
            profiles = ("seed", "requests", "collect", "vary") if name == names[0] else ("evaluate",)
            descriptors, schemas = {}, {}
            for operation in profiles:
                selector = ["--operation", operation] if operation != "evaluate" else []
                descriptors[operation] = json.loads(self.run(["docker", "run", "--rm", "--network", "none", tag,
                    "describe", *selector, "--image-sha256", digest.removeprefix("sha256:")]))
                for kind in (("input", "output") if operation != "evaluate" else ("input", "output", "policy")):
                    raw = self.run(["docker", "run", "--rm", "--network", "none", tag, "schema", *selector,
                                   "--direction" if operation != "evaluate" else "--kind", kind])
                    ports = descriptors[operation]["tool"]["outputs" if kind == "output" else "inputs"]
                    port = next(port for port in ports if (port["name"] == "policy") == (kind == "policy"))
                    assert hashlib.sha256(raw).hexdigest() == port["schema_ref"]["sha256"]
                    filename = operation + "-" + kind + ".json"
                    (context / filename).write_bytes(raw)
                    schemas[operation + "." + kind] = {"schema_ref": port["schema_ref"], "file": str(context / filename)}
            other = "amphora_synthetic_objectives" if name == names[0] else "amphora_evolution_search"
            absent = (other, "amphora_campaign_runtime", "amphora_data_artifacts", "sqlalchemy", "rdkit", "torch")
            probe = "import os,importlib.util; assert os.geteuid()==65532; "
            probe += "assert all(importlib.util.find_spec(m) is None for m in " + repr(absent) + ")"
            self.run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", tag, "-c", probe])
            manifest["tools"].append({"package": name, "module": module, "tag": tag, "image_manifest_digest": digest,
                "image_config_digest": built["containerimage.config.digest"], "local_wheels": hashes,
                "offline_wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((final / "wheels").glob("*.whl"))},
                "descriptors": descriptors, "schemas": schemas, "isolated_nonroot_probe": "passed"})
            self.save(manifest)
            print(name + " image/profiles/isolation passed: " + digest, flush=True)
        manifest["golden"] = verify_golden(self.run, manifest["tools"])
        self.save(manifest)
        print("All numeric capability image goldens passed: " + str(self.output / "manifest.json"), flush=True)

    def save(self, manifest):
        (self.output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    ImageBuild(args.output).build(args.base)
