# Amphora | Command catalog and acceptance meaning

Run from the repository root. Core verification requires Python 3.12+, ordinary assertion checking and a full source clone containing the pinned snapshot. Commands below are implemented unless explicitly marked planned.

```sh
python3.12 v2/dev/diligence/cli.py check-plan
python3.12 v2/dev/diligence/cli.py inspect-task DD-010
python3.12 v2/dev/diligence/cli.py verify-source
```

The first validates the task DAG/candidate registry/source pins. The second displays a task contract; it is not task acceptance. The third runs the original PLGA aggregate checker and original twelve historical assertions, then the source dependency guard. It starts no service and fits no model. Historical acceptance remains historical.

Optional arithmetic uses a separately chosen environment with NumPy installed. This task's isolated test environment pins NumPy 1.26.4 and coverage 7.10.7; the core code never installs them:

```sh
python3.12 v2/dev/diligence/cli.py verify-source --bootstrap
```

For an internal capsule, choose a new external directory. No raw attachment is included. This witness is not an investor-approved payload; original historical records need a later disclosure review.

```sh
python3.12 v2/dev/diligence/cli.py build-capsule --output /tmp/amphora-engineering-capsule-new
python3.12 /tmp/amphora-engineering-capsule-new/verify.py
python3.12 /tmp/amphora-engineering-capsule-new/verify.py --bootstrap
python3.12 v2/dev/diligence/cli.py archive-capsule \
  --capsule /tmp/amphora-engineering-capsule-new \
  --output /tmp/Amphora_Engineering_Capsule_New.zip
```

Existing output directories/archives reject. Verification defaults to stdout. The manifest lists every payload member except itself and its detached digest; SHA-256 is an integrity record, not a publisher signature. The capsule accurately reports that it did not rerun the production-source dependency scan.

Focused tests use the existing dev owner without importing production service dependencies:

```sh
python3.12 -m unittest discover -s v2/dev/tests/diligence -v
python3.12 -m coverage run --branch --source=v2/dev/diligence \
  -m unittest discover -s v2/dev/tests/diligence -v
python3.12 -m coverage json -o /tmp/amphora-diligence-coverage-new.json
```

Coverage is an optional development dependency. Existing scientific commands remain available unchanged under `docs/review/plga/README.md`. Full model reproduction is separately opt-in; it is not run by this plan or these commands.

The implemented plan renderer has a separate ReportLab dependency:

```sh
python3 v2/dev/diligence/render_plan.py --output /tmp/Amphora_Diligence_Workplan_New.pdf
```

It renders this engineering plan and task overview. It does not create or approve the future investor systems note/brief. Inspect all rendered pages after any change and bind QA to the exact output hash.

## Explicitly planned interfaces

Investor approved-claim assembly, a `release_gate.py` entry point, package-local link remapping, caption-location enforcement, automatic artifact-freshness closure and active CI remain planned. No command for them is advertised as working. Their task cards give manual acceptance or a proposed future contract. Shared LaTeX templates establish a source/layout starting point, not a completed note or a claimed compiled output.

Exit convention: 0 means all requested required verification completed; 2 means evidence rejection; 3 means a requested environment/dependency is absent. A standard-library source check can pass where a requested NumPy tier correctly returns 3. No fallback may report that requested bootstrap succeeded.
