import argparse
import json

from .runner import run

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
report = run(args.output)
print(json.dumps({"counts": report["counts"], "paid_calls": report["paid_calls"]}))
