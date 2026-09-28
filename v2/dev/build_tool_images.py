"""Build local isolated tool images and preserve actual image/lock/golden evidence."""

import argparse
import hashlib
import json
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from check_boundaries import ROOT, project_specs


def run(command, *, payload=None):
    result = subprocess.run([str(item) for item in command], input=payload,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    if result.returncode:
        raise RuntimeError("Tool image build/probe failed: " + result.stderr[-3000:])
    return result.stdout.strip()


def closure(name, specs):
    needed, pending = set(), [name]
    while pending:
        name = pending.pop()
        if name in needed:
            continue
        needed.add(name)
        _path, config, _module = specs[name]
        pending.extend(config.get("tool", {}).get("amphora", {}).get("public-imports", []))
    return needed


def build(base, output):
    if "@sha256:" not in base:
        raise ValueError("A digest-pinned Python 3.12 base is required")
    output.mkdir(parents=True, exist_ok=False)
    uv = ROOT / ".venv/Scripts/uv.exe"
    specs = {config["project"]["name"]: (path, config, module) for path, config, module in project_specs()}
    tools = ("amphora-numeric-affine", "amphora-sequence-statistics")
    wheels = output / "built-wheels"
    for name in sorted(set.union(*(closure(tool, specs) for tool in tools))):
        run([uv, "build", "--project", specs[name][0], "--wheel", "--out-dir", wheels])
    manifest = {"schema_version": "1", "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "base": base, "platform": "linux/amd64", "tools": []}
    for name in tools:
        project, _config, module = specs[name]
        context = output / name
        context.mkdir()
        requirements = context / "requirements.txt"
        run([uv, "export", "--project", project, "--locked", "--no-dev", "--no-emit-local", "--output-file", requirements])
        local = context / "local"
        local.mkdir()
        wheel_hashes = {}
        for dependency in sorted(closure(name, specs)):
            wheel = next(wheels.glob(dependency.replace("-", "_") + "-*.whl"))
            shutil.copy2(wheel, local / wheel.name)
            wheel_hashes[wheel.name] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        # Download target-platform dependencies with the exact hashes from the owning uv lock.
        download_recipe = context / "Download.Dockerfile"
        download_recipe.write_text(f"FROM {base}\nCOPY requirements.txt /requirements.txt\n"
            "RUN python -m pip download --require-hashes --only-binary=:all: --dest /resolved -r /requirements.txt\n"
            "COPY local /resolved\n", encoding="utf-8")
        tag = "amphora/" + name.removeprefix("amphora-") + ":bp03-" + uuid.uuid4().hex[:12]
        download_tag = tag + "-dependencies"
        run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
             "-f", download_recipe, "-t", download_tag, context])
        container = run(["docker", "create", download_tag])
        try:
            run(["docker", "cp", container + ":/resolved", context / "wheels"])
        finally:
            run(["docker", "rm", container])
        # Only the offline closure enters the final tool build context.
        final_context = context / "image"
        final_context.mkdir()
        shutil.copytree(context / "wheels", final_context / "wheels")
        shutil.copy2(project / "Dockerfile", final_context / "Dockerfile")
        metadata = context / "image-metadata.json"
        run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
             "--build-arg", "PYTHON_BASE=" + base, "--metadata-file", metadata, "-t", tag, final_context])
        image = json.loads(metadata.read_bytes())
        image_digest = image["containerimage.digest"]
        config_digest = image["containerimage.config.digest"]
        inspected = json.loads(run(["docker", "image", "inspect", tag]))[0]
        observed_descriptor = inspected.get("Descriptor", {})
        assert image_digest == observed_descriptor.get("digest") or any(
            digest.endswith("@" + image_digest) for digest in inspected.get("RepoDigests", []))
        assert config_digest in {inspected["Id"], observed_descriptor.get("annotations", {}).get("config.digest")}
        assert inspected["Architecture"] == "amd64" and inspected["Os"] == "linux"
        descriptor = json.loads(run(["docker", "run", "--rm", "--network", "none", tag, "describe",
                                    "--image-sha256", image_digest.removeprefix("sha256:")]))
        golden = json.loads((project / "tests/fixtures/golden.json").read_bytes())
        result = json.loads(run(["docker", "run", "--rm", "--network", "none", "-i", tag, "compute"],
                                payload=json.dumps(golden["input"])))
        assert result == golden["output"]
        sibling = "amphora_sequence_statistics" if module == "amphora_numeric_affine" else "amphora_numeric_affine"
        probe = "import os,importlib.util; assert os.geteuid()==65532; "
        for absent in (sibling, "sqlalchemy", "amphora_campaign_runtime", "amphora_data_artifacts", "rdkit", "torch"):
            probe += f"assert importlib.util.find_spec('{absent}') is None; "
        run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", tag, "-c", probe])
        entry = {"package": name, "module": module, "tag": tag, "image_manifest_digest": image_digest,
            "image_config_digest": config_digest, "local_wheels": wheel_hashes,
            "offline_wheels": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sorted((final_context / "wheels").glob("*.whl"))},
            "descriptor": descriptor, "golden_input": golden["input"], "golden_output": result,
            "isolated_nonroot_probe": "passed"}
        manifest["tools"].append(entry)
        (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(name + " image/golden/isolation passed: " + image_digest, flush=True)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.base, args.output)
