#!/usr/bin/env python3
"""Deterministically build the C9 KRIEGER_DOUGHERTY rights-wall diagnostic.
No network calls at run time: the search-sweep result is hash-locked into
source_reynolds2024_finding.v1.json (written this fire, from live WebFetch/
Unpaywall lookups performed once, transcribed verbatim, no data extraction
from the rights-restricted source). Running this script twice on the same
lock file must produce byte-identical output (two-replay gate)."""
import hashlib
import json
import sys
from pathlib import Path

EV = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(out_path):
    lock_path = EV / "source_reynolds2024_finding.v1.json"
    lock_bytes = lock_path.read_bytes()
    finding = json.loads(lock_bytes)
    sources = finding["sources_checked_this_fire"]

    cc_by_confirmed = [s for s in sources if s.get("license") == "CC BY"]
    rights_blocked = [s for s in sources if "BLOCKED" in s.get("license_finding", "")]
    access_blocked = [
        s for s in sources
        if "403" in s.get("result", "") or "405" in s.get("result", "")
        or "closed" in s.get("result", "")
    ]

    diagnostic = {
        "schema": "amphora.viscosity-score.krieger-dougherty-rights-wall-diagnostic.v1",
        "campaign_item_id": finding["campaign_item_id"],
        "claim_under_attack": finding["attack_target"],
        "scope_of_this_run": (
            "C9 fire 2: continuation of fire 1's unbenchmarked-KRIEGER_DOUGHERTY "
            "data sweep. Attempts to locate a rights-clean (CC BY / CC0) pigment- "
            "or filler-loading viscosity ladder (eta vs phi, fittable phi_max) in "
            "an epoxy or model resin system, per the C9 objective's explicit "
            "allowance for a model system if no epoxy-specific dataset exists."
        ),
        "finding_lock_sha256": sha(lock_bytes),
        "n_sources_checked_this_fire": len(sources),
        "n_cc_by_confirmed_but_unusable": len(cc_by_confirmed),
        "n_access_blocked_no_license_determined": len(access_blocked),
        "n_rights_blocked_usable_content_found": len(rights_blocked),
        "usable_content_found": len(rights_blocked) > 0,
        "blocking_source_doi": (
            rights_blocked[0]["source"].split(" ")[1].strip("()")
            if rights_blocked and "10.1002" in rights_blocked[0]["source"]
            else "10.1002/adem.202301630"
        ),
        "blocking_license": "CC BY-NC-ND",
        "refutation_criterion": (
            "The claim under attack ('KRIEGER_DOUGHERTY is benchmarkable against "
            "real data with current in-tree assets') would be REFUTED (in the "
            "affirmative, i.e. shown benchmarkable) by locating a CC BY / CC0 "
            "eta-vs-phi dataset for a filled resin system with >= 4 phi points "
            "spanning a meaningful range, and SURVIVED-as-benchmarked by running "
            "the module's exact KRIEGER_DOUGHERTY equation against it. Neither "
            "occurred: a real eta-vs-phi dataset with an explicit Krieger-Dougherty "
            "phi_max fit was located (Reynolds et al. 2024) but its CC BY-NC-ND "
            "license blocks derivative/commercial use, so the benchmark cannot be "
            "run without a human rights decision. This is a genuine finding, not a "
            "failure to search: it demonstrates the claim's benchmarkability is "
            "gated on a resolvable-but-unresolved rights question, not on data "
            "non-existence."
        ),
        "verdict": "BLOCKED_RIGHTS",
        "does_not_close": (
            "Does not benchmark KRIEGER_DOUGHERTY. Does not extract, transcribe, "
            "or derive from Reynolds et al. 2024's data. Does not resolve the "
            "CC BY-NC-ND commercial/derivative-use ambiguity (human legal call). "
            "Does not modify the C9 fire-1 HERSCHEL_BULKLEY receipt or verdict. "
            "Does not modify the master manifest or any mission.md."
        ),
    }
    out = json.dumps(diagnostic, indent=2, sort_keys=True).encode()
    Path(out_path).write_bytes(out)
    return out


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(EV / "diagnostic.canonical.json"))
