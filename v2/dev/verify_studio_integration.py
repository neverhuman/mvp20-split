"""Independent Studio source installs with actual installed Runtime/solver peers."""

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from verify_graphs import verify
from verify_studio import ROOT, stage_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--authoring", action="store_true", help="Include actual draft and emergency command consumers")
    args = parser.parse_args()
    node, npm = shutil.which("node"), shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not node or not npm:
        raise SystemExit("Node24 and npm required")
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "HOME"}}
    with tempfile.TemporaryDirectory(prefix="amphora-studio-integration-") as directory:
        root = Path(directory).resolve()
        assert root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        installs, pins = {}, {}
        for label in ("original", "replacement"):
            workspace = root / label
            workspace.mkdir()
            staged, sources, schemas = stage_source(workspace)
            for command in ([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
                            [node, "scripts/verify.mjs"]):
                result = subprocess.run(command, cwd=staged, env=env, capture_output=True, text=True,
                    encoding="utf-8", timeout=180, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                if result.returncode:
                    raise SystemExit("Independent Studio build failed: " + result.stdout[-2000:] + result.stderr[-2000:])
            installs[label] = str(staged)
            count = re.search(r"(?:tests|pass)\s+(\d+)", result.stdout)
            assert count, "Node test count missing"
            pins[label] = {"source_sha256": sources, "public_schema_pins": schemas, "tests": int(count.group(1))}
        probe = "authoring_probe.py" if args.authoring else "probe.py"
        verify(args.images, "observations", probe_override=ROOT / "studio/tests/integration" / probe,
            extra_config={"studio": installs, "studio_pins": pins, "node": node,
                          "evidence": str(ROOT / ".test-results/studio-integration")})


if __name__ == "__main__":
    main()
