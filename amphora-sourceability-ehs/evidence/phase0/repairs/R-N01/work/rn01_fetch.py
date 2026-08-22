#!/usr/bin/env python3
"""R-N01 fire 1: fresh independent live PubChem CAS/CID fetch for the 5
canonical epoxy-amine hardeners, cached verbatim to work/raw/ for a
byte-stable two-replay diagnostic. Fetched 2026-08-03, independent of the
prior (wrong-key) fire's benchmarks/ghs-clp-cid-attribution-audit-v1/raw/
cache -- new HTTP round-trips, not a copy."""
import json
import time
from pathlib import Path

import requests

RAW = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/work/raw")
UA = {"User-Agent": "amphora-phase0-cron-audit/1.0 (falsification-audit; contact techie@amphora.bio)"}

CANDIDATES = {
    "IPDA": {"cas": "2855-13-2", "claimed_cid": 6944},
    "DDS": {"cas": "80-08-0", "claimed_cid": 2955},
    "DETA": {"cas": "111-40-0", "claimed_cid": 8111},
    "TETA": {"cas": "112-24-3", "claimed_cid": 5565},
    "m-XDA": {"cas": "1477-55-0", "claimed_cid": 15642},
}


def get(url):
    for attempt in range(3):
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200:
            return r.json()
        time.sleep(1.5)
    r.raise_for_status()


def save(name, obj):
    (RAW / name).write_text(json.dumps(obj))
    print("saved", name)


def main():
    for name, meta in CANDIDATES.items():
        cas = meta["cas"]
        claimed_cid = meta["claimed_cid"]
        key = name.replace("-", "")

        # 1. CAS -> CID name-search resolution
        cas_json = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/cids/JSON")
        save(f"cas_to_cid_{key}.json", cas_json)
        time.sleep(0.4)
        real_cid = cas_json["IdentifierList"]["CID"][0]

        # 2. claimed CID -> identity property lookup
        claimed_prop = get(
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{claimed_cid}/property/IUPACName,MolecularFormula,CanonicalSMILES/JSON")
        save(f"claimed_cid_identity_{key}_{claimed_cid}.json", claimed_prop)
        time.sleep(0.4)

        # 3. real (CAS-correct) CID -> identity property lookup (always fetch,
        #    even when real_cid == claimed_cid, for a complete independent record)
        if real_cid != claimed_cid:
            real_prop = get(
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/property/IUPACName,MolecularFormula,CanonicalSMILES/JSON")
            save(f"real_cid_identity_{key}_{real_cid}.json", real_prop)
            time.sleep(0.4)

        # 4. PUG-View GHS Classification for the real (CAS-correct) CID --
        #    always fetch this so we have the correct-record H-codes for
        #    every candidate, not just the mismatched pair.
        ghs = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{real_cid}/JSON/?heading=GHS+Classification")
        save(f"ghs_pugview_real_{key}_{real_cid}.json", ghs)
        time.sleep(0.4)

        # 5. PUG-View GHS Classification for the claimed CID too (so we can
        #    show exactly which wrong-chemical page the receipt's H334 etc.
        #    traces to), only when it differs from the real one.
        if real_cid != claimed_cid:
            ghs_claimed = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{claimed_cid}/JSON/?heading=GHS+Classification")
            save(f"ghs_pugview_claimed_{key}_{claimed_cid}.json", ghs_claimed)
            time.sleep(0.4)

        print(name, "cas", cas, "claimed_cid", claimed_cid, "real_cid_from_cas", real_cid, "match", claimed_cid == real_cid)


if __name__ == "__main__":
    main()
