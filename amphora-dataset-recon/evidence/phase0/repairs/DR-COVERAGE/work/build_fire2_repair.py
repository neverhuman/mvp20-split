#!/usr/bin/env python3
"""Fire 2/2 repair for DR-COVERAGE: converts the 10 triple-null coverage-map
rows identified by fire 1 into explicit commissioned-measurement candidates.
Supersede-never-rewrite: writes a NEW coverage-map.v2.json; never edits
evidence/ledgers/coverage-map.v1.json in place.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"
ITEM = MOD / "evidence/phase0/repairs/DR-COVERAGE"
WORK = ITEM / "work"

FIRE1_COVERAGE_MAP_SHA = "5a2fda9a450d70441f650eba7ec48416f8b5856331b0927dd398634be83500f1"
FIRE1_DATASET_LEDGER_SHA = "a4e8b70e434ee99fe7704451b826c8e2d73bbaa16a6d196788149ff6b458d418"
FIRE2_ID = "20260811T120001-531794-e1706ed51e19"


def sha(b):
    return hashlib.sha256(b).hexdigest()


CONVERSIONS = {
    "corrosion-database-ja": (
        "No open ja national corrosion-materials-database source clears the "
        "rights-clarity floor (PoLyInfo and MatNavi DataSheet Collection No.18 "
        "both REJECTED on Terms-of-Use grounds) -- an honest empty result, per "
        "rule 7 ('An empty search result converts; it never pads and never "
        "disappears'). Converts to a commissioned-measurement candidate: "
        "commission salt-fog / cyclic-corrosion panel testing (JIS Z 2371, the "
        "Japanese-market analogue of ISO 9227) on the portfolio's own "
        "DGEBA-amine + zinc-rich-primer coating stack, feeding directly into "
        "amphora-public-corrosion-benchmark and amphora-barrier-corrosion-score "
        "in place of the rights-blocked NIMS-custodied database."
    ),
    "cure-kinetics-adjacent-epoxy-systems-iberian": (
        "Both Iberian PhD theses located are disqualified for this gap's "
        "direct-chemistry scope (Imar 1994 REJECTED, no accessible full text; "
        "Morancho 1997 RECOMMENDED but serves "
        "amphora-dibenedetto-vitrification-cure-bounds / "
        "amphora-network-tg-protocol-curation as ledger entry "
        "DR-LANG-IBERIAN-DSL-03, not this gap's amphora-cure-kinetics target, "
        "and its chemistry is disclosed as adjacent/non-DGEBA -- correctly not "
        "double-counted here) -- an honest empty result for a DGEBA/"
        "marine-coating-specific Iberian cure-kinetics source, per rule 7. "
        "Converts to a commissioned-measurement candidate: commission "
        "DSC/Kissinger-protocol (ASTM E698) non-isothermal cure-kinetics runs "
        "on the portfolio's own DGEBA + amine-hardener formulations, serving "
        "amphora-cure-kinetics directly rather than via adjacent-chemistry "
        "extrapolation."
    ),
    "cure-kinetics-nl": (
        "No dedicated Dutch-language amine-cure-kinetics dataset or thesis was "
        "found despite a genuine native-nl query (surfaced only international "
        "English-language DSC/Kissinger literature) and an English "
        "TU-Delft-site-restricted follow-up (surfaced only off-topic records) "
        "-- an honest empty result, per rule 7. Converts to a "
        "commissioned-measurement candidate: commission DSC/Kissinger-protocol "
        "(ASTM E698) cure-kinetics plus isothermal pot-life/gel-time "
        "measurements on the portfolio's own DGEBA-amine formulations, serving "
        "amphora-cure-kinetics and amphora-cure-potlife-gate in place of the "
        "unresolved nl-market source."
    ),
    "marine-coating-ks-standard-mapping-ko": (
        "No ship-hull-specific KS anti-corrosion-paint standard number was "
        "found despite two differently-phrased native-ko searches (queries 3 "
        "and 11), mirroring identical ja/de/ru findings for this same "
        "sub-question -- an honest empty result, per rule 7. Converts to a "
        "commissioned-measurement candidate: direct outreach to KATS (Korean "
        "Agency for Technology and Standards) or a KR classification society "
        "to confirm whether a ship-hull-specific KS analogue to ISO 12944 "
        "exists, before amphora-ip-fto-guard or amphora-owk-adhesion cites a "
        "KS number for this scope element."
    ),
    "national-corrosion-testing-institute-pl-cs": (
        "SVUOM's 'Korozni mapy materialu CR' Czech national "
        "atmospheric-corrosivity product was confirmed to exist via a "
        "KOM-journal citation, but both the custodian site (svuom.cz) and the "
        "describing article's PDF were network-unreachable this fire "
        "(WebFetch and raw curl both blocked, same diagnostic pattern "
        "PROBE-WEB recorded for CNKI) -- an honest empty result for a "
        "directly-readable source (not a negative-existence finding), per "
        "rule 7. Converts to a commissioned-measurement candidate: a direct "
        "written data-access request to SVUOM (Czech Republic) for the "
        "Korozni mapy materialu CR extract or its licensing terms, since "
        "access is blocked at the network level from this host rather than "
        "the data being unavailable in principle."
    ),
    "ship-coating-dataset-ko-unresolved": (
        "해양환경공단_선박의_도장결함과_대책 "
        "(Korea Marine Environment Management Corporation, 'Ship Coating "
        "Defects and Countermeasures') is the single most gap-relevant title "
        "surfaced this fire, but its data.go.kr detail-page URL could not be "
        "independently re-resolved across 3 separate queries -- per this "
        "item's own refutation criterion an unresolved native-script citation "
        "is not scored as a disposition candidate, an honest empty result per "
        "rule 7. Converts to a commissioned-measurement candidate: direct "
        "data.go.kr portal registration and native-ko catalog search (outside "
        "this fire's DEGRADED-fetch tooling) to resolve the stable record URL, "
        "or failing that a direct written request to the Korea Marine "
        "Environment Management Corporation for the underlying dataset."
    ),
    "ship-hull-antifouling-standard-mapping-fr": (
        "No French/AFNOR ship-hull-specific antifouling/anticorrosive paint "
        "standard number was found, only a general AFNOR 'pigment "
        "antisalissure' property definition and the general NF EN ISO 12944 "
        "(already captured elsewhere) -- an honest empty result mirroring the "
        "identical de and ja findings for this same scope element, per rule 7. "
        "Converts to a commissioned-measurement candidate: direct outreach to "
        "AFNOR or a French classification society (Bureau Veritas) to confirm "
        "whether a ship-hull-specific antifouling/anticorrosive standard "
        "beyond the generic NF EN ISO 12944 exists, before amphora-ip-fto-guard "
        "or amphora-owk-adhesion cites one."
    ),
    "ship-hull-antifouling-standard-mapping-iberian": (
        "No Spanish/Portuguese/Brazilian ship-hull-specific antifouling/"
        "anticorrosive paint standard number was found, only academic/trade "
        "literature and the general UNE-EN ISO 12944 / NP EN ISO 12944 / "
        "NBR-referenced ISO 12944 (already captured elsewhere) -- an honest "
        "empty result mirroring the identical de, fr, and ja findings for this "
        "same scope element, per rule 7. Converts to a commissioned-measurement "
        "candidate: direct outreach to AENOR (Spain), IPQ (Portugal), or ABNT "
        "(Brazil) to confirm whether a ship-hull-specific antifouling/"
        "anticorrosive standard beyond generic ISO 12944 exists in the Iberian/"
        "Lusophone corpus, before amphora-ip-fto-guard or amphora-owk-adhesion "
        "cites one."
    ),
    "ship-hull-antifouling-standard-mapping-it": (
        "No Italian/UNI ship-hull-specific antifouling/anticorrosive paint "
        "standard number was found, only general antifouling-application "
        "practitioner pages -- an honest empty result mirroring the identical "
        "nl/de/ja/fr findings for this same scope element, per rule 7. "
        "Converts to a commissioned-measurement candidate: direct outreach to "
        "UNI or RINA (Italian classification society) to confirm whether a "
        "ship-hull-specific antifouling/anticorrosive standard beyond generic "
        "ISO 12944 exists in the Italian corpus, before amphora-ip-fto-guard or "
        "amphora-owk-adhesion cites one."
    ),
    "ship-hull-antifouling-standard-mapping-nl": (
        "No Dutch/NEN ship-hull-specific antifouling/anticorrosive paint "
        "standard number was found, only the general NEN standards committee "
        "'Verfwaren, metallieke en anorganische deklagen en corrosie' and the "
        "general NEN-EN-ISO 12944 (already captured elsewhere) -- an honest "
        "empty result mirroring the identical de/ja/fr findings for this same "
        "scope element, per rule 7. Converts to a commissioned-measurement "
        "candidate: direct outreach to NEN or a Netherlands-based "
        "classification-society office to confirm whether a "
        "ship-hull-specific antifouling/anticorrosive standard beyond generic "
        "NEN-EN-ISO 12944 exists in the Dutch corpus, before "
        "amphora-ip-fto-guard or amphora-owk-adhesion cites one."
    ),
}


def main():
    cm_path = LEDGERS / "coverage-map.v1.json"
    dl_path = LEDGERS / "dataset-ledger.v1.jsonl"
    cm_bytes = cm_path.read_bytes()
    dl_bytes = dl_path.read_bytes()
    assert sha(cm_bytes) == FIRE1_COVERAGE_MAP_SHA, "live coverage-map.v1.json changed since fire 1 snapshot"
    assert sha(dl_bytes) == FIRE1_DATASET_LEDGER_SHA, "live dataset-ledger.v1.jsonl changed since fire 1 snapshot"

    cm = json.loads(cm_bytes)
    assert set(CONVERSIONS) <= {g["gap_id"] for g in cm["gaps"]}

    patched = 0
    for g in cm["gaps"]:
        if g["gap_id"] in CONVERSIONS:
            triple = (g.get("best_recommended"), g.get("best_conditional"),
                       g.get("commissioned_measurement_candidate"))
            assert all(v is None for v in triple), f"{g['gap_id']} was not triple-null as expected"
            g["commissioned_measurement_candidate"] = CONVERSIONS[g["gap_id"]]
            patched += 1
    assert patched == 10, patched

    cm["coverage_map_version"] = "v2"
    cm["repair_fire_id"] = FIRE2_ID
    cm["repair_campaign_item_id"] = "DR-COVERAGE"
    cm["supersedes"] = {
        "superseded_path": "amphora-dataset-recon/evidence/ledgers/coverage-map.v1.json",
        "superseded_sha256": FIRE1_COVERAGE_MAP_SHA,
        "superseded_deleted_or_modified": False,
        "reason": (
            "Fire 20260811T110001-7123-94961fa526cc (DR-COVERAGE fire 1/2) found "
            "10 of 64 gaps[] rows serving a real module_gap had best_recommended, "
            "best_conditional, AND commissioned_measurement_candidate all null -- "
            "an honest empty search result disclosed in the note prose but never "
            "structurally converted, violating rule 7 and this item's own "
            "done_criterion. This v2 file supersedes v1 by filling all 10 rows' "
            "commissioned_measurement_candidate field with an explicit "
            "lab-in-the-loop conversion sentence, using the same pattern already "
            "present on 12 other rows in v1 (e.g. jis-eew-testdata-annex-ja). "
            "v1.json is left byte-unmodified at its original path; this is a new "
            "artifact, not an in-place edit."
        ),
        "repaired_gap_ids": sorted(CONVERSIONS),
    }

    out_bytes = json.dumps(cm, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8")
    out_path = WORK / "coverage-map.v2.candidate.json"
    out_path.write_bytes(out_bytes)
    print("WROTE", out_path, "sha256", sha(out_bytes), "patched", patched)


if __name__ == "__main__":
    main()
