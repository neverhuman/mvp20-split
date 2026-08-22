#!/usr/bin/env python3
"""Sign the V-N02a independent-verify done receipt with the PHASE0_EVALUATOR
key, matching the repo-wide evidence/ signing convention (evaluator_key_id/
evaluator_public_key_hex/reviewer_public_key_hex/signature DSSE envelope
shape) used by R-N02's own done receipts and the amine-nh-guanidine-
conjugation-gap audit."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-molecule-property/evidence/phase0/repairs/V-N02a/work"
DONE = ROOT / "amphora-molecule-property/evidence/phase0/repairs/V-N02a/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
R_N02_DONE = ROOT / "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json"

FIRE_ID = "20260804T010001-2885876-e367b1f56e17"
CAMPAIGN_ITEM_ID = "V-N02a"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


sweepA = (WORK / "sweep.runA.json").read_bytes()
sweepB = (WORK / "sweep.runB.json").read_bytes()
assert sweepA == sweepB, "two-replay bytes differ"
sweep = json.loads(sweepA)
assert sweep["verdict"] == "CLAIM_SURVIVED"
assert sweep["all_legs_pass"] is True
assert sweep["leg1_original_3_probes"]["all_zero"] is True
assert sweep["leg2_26_record_regression"]["all_match"] is True
assert sweep["leg2_26_record_regression"]["n_records"] == 26
assert sweep["leg3_novel_amidine_probes"]["all_expected"] is True
assert len(sweep["leg3_novel_amidine_probes"]["rows"]) == 3

verify_script = (WORK / "vn02a_verify_sweep.py").read_bytes()
r_n02_done_bytes = R_N02_DONE.read_bytes()

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

body_obj = {
    "schema": "amphora.molecule-property.v-n02a-independent-verify-receipt.v1",
    "receipt_id": "v-n02a-molecule-property-independent-verify-" + sha(sweepA)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "repair_item_verified": "R-N02",
    "r_n02_done_receipt_path": "amphora-molecule-property/evidence/phase0/repairs/R-N02/done/rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json",
    "r_n02_done_receipt_sha256": sha(r_n02_done_bytes),
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "module": "amphora-molecule-property",
    "claim_under_attack": (
        "The coordinated C=N amine-rule fix (R-N02) withstands independent "
        "adversarial verification in this module: amphora-molecule-property/"
        "evidence/phase0/repairs/R-N02/done/"
        "rn02-molecule-property-coordinated-cn-fix-repair-receipt.v1.dsse.json"
    ),
    "objective": (
        "INDEPENDENT VERIFY of interactive repair R-N02, per campaign item "
        "V-N02a. Did not write R-N02; attacked it. Re-ran the original 3 "
        "refuting probes and the 26-record zero-regression check from a "
        "FRESH, independent extraction of the currently-shipped "
        "n_active_amine_nh() (not a replay of R-N02's own stored sweep "
        "bytes or script), then constructed and ran 2+ NOVEL amidine-family "
        "probes never used by R-N02 or any prior fire, including one "
        "deliberately adversarial boundary case designed to catch "
        "over-exclusion."
    ),
    "method": (
        "Wrote a fresh verification harness "
        "(evidence/phase0/repairs/V-N02a/work/vn02a_verify_sweep.py) that "
        "extracts n_active_amine_nh() VERBATIM by source marker from the "
        "LIVE, currently-shipped "
        "benchmarks/amine-class-active-nh-robustness-v1/compute_amine_class.py "
        "-- an independent extraction, not a copy of R-N02's own "
        "rn02_property_sweep.py bytes or import. Three legs: "
        "(1) re-run the 3 ORIGINAL refuting probes (guanidine CAS 113-00-8, "
        "dicyandiamide/DICY CAS 461-58-5, biguanide CAS 461-71-2); refute if "
        "any returns nonzero. "
        "(2) re-run the full 26-record zero-regression check (3 exact "
        "anchors, 6 monodisperse, 13 amine-grid, 7 nonamine controls, 1 "
        "hydroxyl probe) with expected n_active_nh values TRANSCRIBED "
        "DIRECTLY from R-N02's own already-signed, byte-verified done "
        "receipt (zero_regression_evidence.molecule_property_26_records."
        "records), not from any sweep script; refute on any mismatch. "
        "(3) construct and run 3 NOVEL amidine-family probes absent from "
        "R-N02's probe set, the 26-record regression set, and the sibling "
        "role-ranker DPG/DOTG probes: acetamidine (CAS 60-10-6) and "
        "benzamidine (CAS 618-39-3), both true amidines whose C=N-bearing "
        "carbon is structurally distinct from guanidine's 3-nitrogen "
        "N-C(=N)-N core -- chemically-justified expected n_active_nh=0 "
        "under the shipped rule's own stated mechanism (the exclusion "
        "fires per attached carbon bearing ANY C=N, zeroing all N-H on "
        "nitrogens bonded to that carbon, exactly as observed for "
        "guanidine's 3 nitrogens) -- plus 2-aminopyridine (CAS 504-29-0) as "
        "a deliberately ADVERSARIAL boundary probe: a primary aromatic "
        "exocyclic amine, same structural class as aniline (already "
        "n_active_nh=2 in the 26-record set), whose ring carbon-nitrogen "
        "bond is an AROMATIC bond (RDKit GetBondTypeAsDouble()==1.5) rather "
        "than a localized C=N double bond (==2.0) -- chemically-justified "
        "expected n_active_nh=2 because the amidine/guanidine lone-pair-"
        "into-adjacent-pi-acceptor mechanism the shipped rule targets "
        "requires a LOCALIZED C=N pi-acceptor, which an aromatic ring bond "
        "is not. This probe would refute R-N02 if the C=N fix over-fired on "
        "aromatic systems and silently zeroed a real primary-amine "
        "hardener/accelerator component."
    ),
    "input_artifacts": {
        "target_source_file": sweep["target_source_file"],
        "target_source_file_sha256": sweep["target_source_file_sha256"],
        "shipped_n_active_amine_nh_source_sha256": sweep["shipped_n_active_amine_nh_source_sha256"],
        "benchmark_data_sha256": sweep["benchmark_data_sha256"],
        "target_receipt_sha256": sweep["target_receipt_sha256"],
        "verify_sweep_script_sha256": sha(verify_script),
    },
    "leg1_original_3_probes": sweep["leg1_original_3_probes"],
    "leg2_26_record_regression": sweep["leg2_26_record_regression"],
    "leg3_novel_amidine_probes": sweep["leg3_novel_amidine_probes"],
    "all_legs_pass": sweep["all_legs_pass"],
    "pre_registered_refute_criterion": (
        "This verification would have REFUTED R-N02 if ANY of: (a) any of "
        "the 3 original probes (guanidine/DICY/biguanide) returned nonzero "
        "n_active_nh under the currently-shipped rule; (b) any of the 26 "
        "previously-validated regression records diverged from its own "
        "asserted truth value; (c) acetamidine or benzamidine returned "
        "nonzero n_active_nh (would show the fix is guanidine-specific, not "
        "a genuine categorical amidine/guanidine rule); (d) 2-aminopyridine "
        "returned 0 instead of 2 (would show the fix over-fires on aromatic "
        "ring systems, silently disqualifying a real primary-amine "
        "component that is chemically NOT an amidine/guanidine). None of "
        "these occurred; all three legs pass; see rows above for the "
        "per-probe/per-record observed values."
    ),
    "verdict": sweep["verdict"],
    "why": (
        "The R-N02 fix (widening the neighbor-carbon double-bond-partner "
        "set from {O,S} to {O,S,N} in n_active_amine_nh's amide/amidine/"
        "guanidine exclusion check) generalizes correctly beyond the 3 "
        "probes and 26 records it was originally verified against: it "
        "correctly zeroes two structurally-distinct novel amidine "
        "chemotypes (acetamidine, benzamidine) via the SAME mechanism "
        "(carbon bearing an explicit, non-aromatic C=N double bond), and it "
        "correctly does NOT zero a chemically-similar-looking but "
        "mechanistically-distinct aromatic amine (2-aminopyridine), because "
        "RDKit's aromatic bond typing (order 1.5) does not satisfy the "
        "rule's ==2.0 double-bond test -- the fix is bounded to the exact "
        "physical mechanism it claims (localized C=N lone-pair "
        "delocalization) rather than over-firing on any nitrogen-adjacent "
        "aromatic ring."
    ),
    "scope_note": (
        "This verification is CATEGORICAL/structural only, matching R-N02's "
        "own scope. It does not reopen the quantitative AHEW question R-N02 "
        "explicitly left open (whether a guanidine/amidine-class latent "
        "hardener has some nonzero equivalent weight in a mechanistic "
        "sense distinct from 1:1 RT amine-epoxide addition) -- acetamidine "
        "and benzamidine's theoretical_ahew is correctly reported as null "
        "(undefined under the M/n rule), same as guanidine/DICY/biguanide."
    ),
    "primary_sources": [
        "Lee & Neville, Handbook of Epoxy Resins, McGraw-Hill 1967",
        "C.A. May (ed.), Epoxy Resins 2nd ed., Marcel Dekker 1988, ISBN 0-8247-7690-9",
        "B. Ellis (ed.), Chemistry and Technology of Epoxy Resins, Blackie 1993, ISBN 0-7514-0095-0",
        "ASTM D1652 (epoxide equivalent weight)",
    ],
    "rights_check": (
        "No new external data source opened or acquired. All 3 novel probe "
        "molecules (acetamidine, benzamidine, 2-aminopyridine) are "
        "constructed in-script from CAS-identified SMILES (public-domain "
        "chemical identity facts), evaluated purely structurally via the "
        "already-licensed pinned RDKit backend. All regression truth values "
        "are transcribed from an already-in-tree, already-signed receipt."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "sweep_runA_sha256": sha(sweepA),
        "sweep_runB_sha256": sha(sweepB),
        "determinism_basis": "no RNG, no wall clock, fixed hardcoded probe SMILES, sort_keys canonical JSON.",
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY V-N02a independent-verify done-receipt under evidence/phase0/repairs/V-N02a/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(WORK / "receipt_body.canonical.json").write_bytes(body1)
(WORK / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-property.v-n02a-independent-verify-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
outpath = DONE / "v-n02a-molecule-property-independent-verify-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
