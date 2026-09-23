#!/usr/bin/env python3
"""R-N01 fires 2-3: fresh independent live PubChem fetch (2026-08-04), a
NEW HTTP round-trip distinct from fire 1's (2026-08-03) work/raw/ cache, to
build the superseding hazard-card receipt with CAS-correct CIDs for all 5
canonical epoxy-amine candidates."""
import json
import time
from pathlib import Path

import requests

RAW = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-sourceability-ehs/evidence/phase0/repairs/R-N01/work/fire2_raw")
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "amphora-phase0-cron-audit/1.0 (falsification-audit; contact techie@amphora.bio)"}

CANDIDATES = {
    "IPDA": {"cas": "2855-13-2", "claimed_cid": 6944},
    "DDS": {"cas": "80-08-0", "claimed_cid": 2955},
    "DETA": {"cas": "111-40-0", "claimed_cid": 8111},
    "TETA": {"cas": "112-24-3", "claimed_cid": 5565},
    "mXDA": {"cas": "1477-55-0", "claimed_cid": 15642},
}


def get(url):
    for attempt in range(4):
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200:
            return r.json()
        time.sleep(1.5)
    r.raise_for_status()


def save(name, obj):
    (RAW / name).write_text(json.dumps(obj))
    print("saved", name)


def main():
    for key, meta in CANDIDATES.items():
        cas = meta["cas"]
        claimed_cid = meta["claimed_cid"]

        cas_json = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{cas}/cids/JSON")
        save(f"cas_to_cid_{key}.json", cas_json)
        time.sleep(0.4)
        real_cid = cas_json["IdentifierList"]["CID"][0]

        real_prop = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{real_cid}/property/IUPACName,MolecularFormula,CanonicalSMILES/JSON")
        save(f"real_cid_identity_{key}_{real_cid}.json", real_prop)
        time.sleep(0.4)

        real_ghs = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{real_cid}/JSON/?heading=GHS+Classification")
        save(f"ghs_pugview_real_{key}_{real_cid}.json", real_ghs)
        time.sleep(0.4)

        if real_cid != claimed_cid:
            claimed_prop = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{claimed_cid}/property/IUPACName,MolecularFormula,CanonicalSMILES/JSON")
            save(f"claimed_cid_identity_{key}_{claimed_cid}.json", claimed_prop)
            time.sleep(0.4)
            claimed_ghs = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{claimed_cid}/JSON/?heading=GHS+Classification")
            save(f"ghs_pugview_claimed_{key}_{claimed_cid}.json", claimed_ghs)
            time.sleep(0.4)

        print(key, "cas", cas, "claimed_cid", claimed_cid, "real_cid_from_cas", real_cid, "match", claimed_cid == real_cid)


if __name__ == "__main__":
    main()
