"""Run the integration-owned public-owner replica matrix in an isolated SDK interpreter."""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("replica_environment", Path(__file__).with_name("environment.py"))
environment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(environment)


def main():
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-replica-peers-") as directory:
        e = environment.Environment(config, Path(directory))
        try:
            e.setup()
            cases = environment.load("replica_scenarios", Path(__file__).with_name("scenarios.py"))
            cases.run(e, environment.HTTP)
            if config.get("previous_images"):
                environment.load("replica_recovery", Path(__file__).with_name("recovery.py")).run(e, environment.HTTP)
                environment.load("replica_cutover", Path(__file__).with_name("cutover.py")).run(e, environment.HTTP)
            e.save("passed")
            print("Actual registry/replica matrix passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
