#!/usr/bin/env python3
"""W-EHS1: fresh independent live fetch (2026-08-05) of the two regulatory
sources the campaign item names for DDS's H351 (suspected carcinogen) flag:
(1) PubChem PUG-View aggregated GHS Classification for CID 2955 (DDS/dapsone),
(2) IARC's own official "Agents Classified by the IARC Monographs" live data
file (served from webapi.iarc.who.int, the same endpoint that backs the
public https://monographs.iarc.who.int/list-of-classifications page).
Both are NEW HTTP round-trips distinct from R-N01 fire 2's 2026-08-04 cache
(which only fetched PubChem, not IARC)."""
import json
import time
from pathlib import Path

import requests

RAW = Path("/home/ubuntu/amphora/build/mvp20-split/amphora-sourceability-ehs/evidence/phase0/repairs/W-EHS1/work/raw")
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "amphora-phase0-cron-audit/1.0 (falsification-audit; contact techie@amphora.bio)"}

DDS_CAS = "80-08-0"
DDS_CID = 2955


def get(url, as_json=True):
    for attempt in range(4):
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code == 200:
            return r.json() if as_json else r.text
        time.sleep(1.5)
    r.raise_for_status()


def main():
    # Source 1: PubChem PUG-View aggregated GHS Classification for CID 2955.
    ghs = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{DDS_CID}/JSON/?heading=GHS+Classification")
    (RAW / f"ghs_pugview_DDS_{DDS_CID}.json").write_text(json.dumps(ghs))
    print("saved pubchem ghs pugview", DDS_CID)
    time.sleep(0.4)

    ident = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{DDS_CID}/property/IUPACName,MolecularFormula,CanonicalSMILES/JSON")
    (RAW / f"identity_DDS_{DDS_CID}.json").write_text(json.dumps(ident))
    print("saved pubchem identity", DDS_CID)
    time.sleep(0.4)

    cas_json = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{DDS_CAS}/cids/JSON")
    (RAW / "cas_to_cid_DDS.json").write_text(json.dumps(cas_json))
    print("saved pubchem cas->cid", DDS_CAS, "->", cas_json["IdentifierList"]["CID"])
    time.sleep(0.4)

    # Source 2: IARC's own official live classification data file (the JS
    # data array backing the public "Agents Classified by the IARC
    # Monographs" list at https://monographs.iarc.who.int/list-of-classifications).
    iarc_js = get("https://webapi.iarc.who.int/loc/loc.app.js", as_json=False)
    (RAW / "iarc_loc_app.js").write_text(iarc_js)
    print("saved iarc loc.app.js", len(iarc_js), "bytes")


if __name__ == "__main__":
    main()
