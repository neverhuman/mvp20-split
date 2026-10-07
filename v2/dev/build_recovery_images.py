"""Qualify the reconstructed test adapter's exact source and corrected evaluator."""

import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path

from build_numeric_images import ImageBuild
from check_boundaries import ROOT
from numeric_image_golden import verify_golden


def verify(base, output, numeric_install, evaluator_install):
    builder = ImageBuild(output)
    builder.build(base)
    manifest = json.loads((builder.output / "manifest.json").read_bytes())
    numeric, evaluator = manifest["tools"]
    for image, installation in ((numeric, numeric_install), (evaluator, evaluator_install)):
        installed = json.loads((installation / "manifest.json").read_bytes())
        assert image["local_wheels"] == installed["wheels"]
    context = builder.output / "reconstructed"
    context.mkdir()
    source = ROOT / "tests/integration/search_recovery/rebuilt_adapter.py"
    shutil.copy2(source, context / "rebuilt_adapter.py")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    # The unique base tag was just built and verified above. Its manifest is retained.
    (context / "Dockerfile").write_text("FROM " + numeric["tag"] + "\n"
        "COPY --chown=65532:65532 rebuilt_adapter.py /app/rebuilt_adapter.py\n"
        'ENTRYPOINT ["python","-I","/app/rebuilt_adapter.py"]\n', encoding="utf-8")
    tag = "amphora/search-reconstruction:bp08-" + uuid.uuid4().hex[:12]
    metadata = context / "image-metadata.json"
    builder.run(["docker", "buildx", "build", "--platform", "linux/amd64", "--load", "--provenance=false",
                 "-f", context / "Dockerfile", "--metadata-file", metadata, "-t", tag, context])
    built = json.loads(metadata.read_bytes())
    inspected = json.loads(builder.run(["docker", "image", "inspect", tag]))[0]
    image_digest = built["containerimage.digest"]
    assert inspected.get("Descriptor", {}).get("digest") == image_digest or any(
        item.endswith("@" + image_digest) for item in inspected.get("RepoDigests", []))
    assert inspected["Architecture"] == "amd64" and inspected["Os"] == "linux"
    profiles = context / "reviewed"
    profiles.mkdir()
    descriptors = {}
    for operation in ("seed", "requests", "collect", "vary"):
        raw = builder.run(["docker", "run", "--rm", "--network", "none", numeric["tag"], "describe",
                           "--operation", operation, "--image-sha256", image_digest.removeprefix("sha256:")])
        descriptors[operation] = json.loads(raw)
        (profiles / (operation + ".json")).write_bytes(raw)
    reconstructed = dict(numeric, tag=tag, image_manifest_digest=image_digest,
        image_config_digest=built["containerimage.config.digest"], descriptors=descriptors,
        base_image_manifest=numeric["image_manifest_digest"], adapter_sha256=digest)
    # Reviewed descriptor files are supplied externally, matching worker deployment.
    # No descriptor or implementation pin is silently synthesized by the adapter.
    def run(command, payload=None):
        if tag in command:
            command = list(command)
            at = command.index(tag)
            operation = command[command.index("--operation") + 1]
            # Docker Desktop cannot bind-mount this NAS-backed Windows workspace.
            # Copy reviewed configuration to a stopped, isolated test container.
            arguments = command[at:] + ["--descriptor", "/reviewed/" + operation + ".json"]
            container = builder.run(["docker", "create", "--network", "none", "-i", *arguments]).decode().strip()
            try:
                builder.run(["docker", "cp", profiles, container + ":/reviewed"])
                return builder.run(["docker", "start", "-a", "-i", container], payload)
            finally:
                builder.run(["docker", "rm", container])
        return builder.run(command, payload)
    golden = verify_golden(run, [reconstructed, evaluator])
    probe = "import hashlib,os,pathlib,importlib.util; assert os.geteuid()==65532; "
    probe += "assert hashlib.sha256(pathlib.Path('/app/rebuilt_adapter.py').read_bytes()).hexdigest()==" + repr(digest) + "; "
    probe += "assert all(importlib.util.find_spec(n) is None for n in ('sqlalchemy','amphora_campaign_runtime','amphora_data_artifacts','amphora_synthetic_objectives','rdkit','torch')); "
    probe += "import runpy,sys; runpy.run_path('/app/rebuilt_adapter.py',run_name='reconstruction_probe'); "
    probe += "assert not any(n.startswith(('amphora_evolution_search.adapter','amphora_evolution_search.capabilities')) for n in sys.modules)"
    builder.run(["docker", "run", "--rm", "--network", "none", "--entrypoint", "python", tag, "-I", "-c", probe])
    manifest.update(profile="search-reconstruction-images-v1", reconstructed=reconstructed,
        reconstructed_golden=golden, isolated_exact_source_probe="passed", paid_calls=0,
        limits=["Offline Linux/amd64 compute qualification only; actual Windows worker transport is separate evidence",
                "Reconstruction reuses the public numeric kernel; not an independent algorithm rewrite",
                "No target-host, cluster, ARM or cross-hardware deterministic-replay claim"])
    builder.save(manifest)
    print("Reconstructed adapter and corrected evaluator images qualified", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    for option in ("output", "numeric-install", "evaluator-install"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    verify(args.base, args.output, args.numeric_install, args.evaluator_install)
