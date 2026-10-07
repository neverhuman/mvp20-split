"""Qualify old/new affine images from exact independently installed closures."""

import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from build_tool_images import build, run
from check_boundaries import ROOT


def verify(base, output, installs):
    output = output.absolute()
    manifest = build(base, output, "affine")
    new = manifest["tools"][0]
    new_install = json.loads((installs / "numeric-new/manifest.json").read_bytes())
    old_install = json.loads((installs / "numeric-old/manifest.json").read_bytes())
    assert new["local_wheels"] == new_install["wheels"]
    old_context = output / "numeric-old"
    old_context.mkdir()
    wheels = old_context / "wheels"
    wheels.mkdir()
    for path in (output / "amphora-numeric-affine/image/wheels").glob("*.whl"):
        if path.name not in new["local_wheels"]:
            shutil.copy2(path, wheels / path.name)
    for name, digest in old_install["wheels"].items():
        path = installs / "numeric-old/wheels" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        shutil.copy2(path, wheels / name)
    recipe = (ROOT / "tools/numeric_affine/Dockerfile").read_text(encoding="utf-8")
    assert recipe.count("amphora-numeric-affine==0.3.0") == 1
    (old_context / "Dockerfile").write_text(recipe.replace("amphora-numeric-affine==0.3.0", "amphora-numeric-affine==0.2.0"), encoding="utf-8")
    tag = "amphora/numeric-affine:topology-old-" + uuid.uuid4().hex[:12]
    metadata = old_context / "image-metadata.json"
    run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
         "--build-arg", "PYTHON_BASE=" + base, "--metadata-file", metadata, "-t", tag, old_context])
    actual = json.loads(metadata.read_bytes())
    digest = actual["containerimage.digest"]
    inspected = json.loads(run(["docker", "image", "inspect", tag]))[0]
    assert inspected["Architecture"] == "amd64" and inspected["Os"] == "linux"
    assert inspected.get("Descriptor", {}).get("digest") == digest or any(value.endswith("@" + digest) for value in inspected.get("RepoDigests", []))
    assert actual["containerimage.config.digest"] in {inspected["Id"], inspected.get("Descriptor", {}).get("annotations", {}).get("config.digest")}
    descriptor = json.loads(run(["docker", "run", "--rm", "--network", "none", tag, "describe", "--image-sha256", digest.removeprefix("sha256:")]))
    assert descriptor["tool"]["binding"]["release"] == "0.2.0"
    result = json.loads(run(["docker", "run", "--rm", "--network", "none", "-i", tag, "compute"], payload=json.dumps(new["golden_input"])))
    assert result == new["golden_output"]
    probe = "import os,importlib.util; assert os.geteuid()==65532; assert all(importlib.util.find_spec(m) is None for m in ('sqlalchemy','amphora_campaign_runtime','amphora_agent_planning','amphora_data_artifacts','rdkit','torch'))"
    run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", tag, "-c", probe])
    old = {"package": "amphora-numeric-affine", "module": "amphora_numeric_affine", "tag": tag,
        "image_manifest_digest": digest, "image_config_digest": actual["containerimage.config.digest"],
        "local_wheels": old_install["wheels"], "offline_wheels": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in wheels.glob("*.whl")},
        "descriptor": descriptor, "golden_input": new["golden_input"], "golden_output": result, "isolated_nonroot_probe": "passed"}
    # Check actual installed schema bytes in both Linux images independently.
    script = "import hashlib,json; from importlib.resources import files; print(json.dumps({k:hashlib.sha256(files('amphora_numeric_affine').joinpath('schemas',k+'.json').read_bytes()).hexdigest() for k in ('input','output')}))"
    for image in (old, new):
        hashes = json.loads(run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", image["tag"], "-c", script]))
        assert hashes == {"input": image["descriptor"]["tool"]["inputs"][0]["schema_ref"]["sha256"],
                          "output": image["descriptor"]["tool"]["outputs"][0]["schema_ref"]["sha256"]}
        image["schema_bytes"] = hashes
    manifest.update(profile="topology-images-v1", tools=[old, new], paid_calls=0,
                    limits=["Offline Linux/amd64 qualification, no cluster deployment or scientific claim"])
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Both topology tool images passed with exact isolated wheel closures", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--installs", required=True, type=Path)
    args = parser.parse_args()
    verify(args.base, args.output, args.installs.absolute())
