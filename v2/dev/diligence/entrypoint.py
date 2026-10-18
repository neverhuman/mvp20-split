"""Copied as verify.py in a capsule; acquire this verifier from reviewed Git."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from diligence.capsule import verify_capsule, MissingEnvironment
from diligence.core import Rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', action='store_true')
    parser.add_argument('--expected-manifest-sha256', help='Digest obtained outside this capsule from a trusted release source')
    args = parser.parse_args()
    try:
        report = verify_capsule(Path(__file__).resolve().parent, args.bootstrap,
                                expected_manifest=args.expected_manifest_sha256)
        code = 0
    except MissingEnvironment as error:
        report = {'status': 'environment_unavailable', 'reason': str(error)}; code = 3
    except (Rejected, OSError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as error:
        report = {'status': 'rejected', 'reason': str(error) if isinstance(error, Rejected) else 'verification_failed'}; code = 2
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
