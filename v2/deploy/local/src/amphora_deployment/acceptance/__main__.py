"""Verify the frozen local evidence ledger without launching services."""

import argparse
import json
from pathlib import Path

from .ledger import MAX_DOCUMENT, AcceptanceLedger, EvidenceError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, required=True)
    parser.add_argument('--evidence-directory', type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.ledger.open('rb') as stream:
            ledger = AcceptanceLedger.from_bytes(stream.read(MAX_DOCUMENT + 1))
        report = ledger.verify(args.evidence_directory)
    except (EvidenceError, OSError) as error:
        report = {'status': 'rejected', 'reason': str(error) if isinstance(error, EvidenceError) else 'ledger_unavailable'}
    print(json.dumps(report, sort_keys=True))
    return 0 if report['status'] == 'verified' else 2


if __name__ == '__main__':
    raise SystemExit(main())
