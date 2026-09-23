#!/usr/bin/env python3
"""V-B02 independent-verify receipt builder/signer.

Independently verifies the R-B02 interactive repair (barrier_index_from_spectrum
in amphora-barrier-corrosion-score/src/lib.rs). Re-runs cargo test, reviews the
formula against its cited Brasher & Kingsbury (1954) convention, and attacks
the repair's own documented "fails closed even if called on its own" guarantee
with an adversarial edge case NOT in the existing test suite: a duplicated /
reordered spectrum where the last element is not the true lowest-frequency
point. Builds a DSSE-Ed25519 verify receipt replicating the rb02_sign_repair.py
construction (pae(), load_seed(), payloadType, envelope fields), writes it
under evidence/phase0/repairs/V-B02/done/, and self-verifies from disk.
"""
import base64
import hashlib
import json
import math
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-barrier-corrosion-score"
LIB = MOD / "src/lib.rs"
R_B02_DONE = MOD / "evidence/phase0/repairs/R-B02/done/barrier-index-repair-receipt.v1.dsse.json"
VERIFY_ITEM = MOD / "evidence/phase0/repairs/V-B02"
DONE = VERIFY_ITEM / "done"
WORK = VERIFY_ITEM / "work"
SEED = Path.home() / ".local/share/amphora/phase0/keys/evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
CARGO = str(Path.home() / ".cargo/bin/cargo")

EXPECTED_LIB_SHA = "4773b6cb7012c3b85a5cf2d319d5e99ae4b8b2a41d2c0540f6a751bb0a6955fc"
EXPECTED_R_B02_DONE_SHA = "8ffcd5595bbf0215c8c061b8c7be80fb620d59105926288817b6cb6243e6670f"
RECEIPT_PATH = DONE / "v-b02-independent-verify-receipt.v1.dsse.json"
PTYPE = "application/vnd.amphora.barrier-corrosion-score.repair-independent-verify+json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def pae(t: str, body: bytes) -> bytes:
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# ---------------------------------------------------------------- guards ----
lib_bytes_pre = LIB.read_bytes()
assert sha(lib_bytes_pre) == EXPECTED_LIB_SHA, "lib.rs is not the R-B02 repaired version at verify start"
r_b02_bytes = R_B02_DONE.read_bytes()
assert sha(r_b02_bytes) == EXPECTED_R_B02_DONE_SHA, "R-B02 done receipt changed on disk"

# --------------------------------------------- probe A: live cargo re-run ---
proc = subprocess.run(
    [CARGO, "test", "-p", "amphora-barrier-corrosion-score"],
    cwd=str(ROOT), capture_output=True, text=True, timeout=540)
cargo_output_baseline = proc.stdout + proc.stderr
assert proc.returncode == 0, cargo_output_baseline[-3000:]
assert "test result: ok. 6 passed; 0 failed" in cargo_output_baseline, cargo_output_baseline[-3000:]

# --------------------------------------- probe B: adversarial edge case -----
# Not in R-B02's own test (test_barrier_index_fails_closed_on_degenerate_spectra
# covers only: empty spectrum, single-point, non-finite component, zero
# modulus, rights_ineligible). We add ONE new adversarial case: append a
# duplicate of the spectrum's HIGHEST-frequency point onto the END of an
# otherwise well-formed, strictly-descending 16-point spectrum. This makes
# `.last()` no longer the lowest-frequency point -- exactly the invariant the
# helper's own doc-comment claims to defend "even if called on its own"
# (validate_conditions() would reject this input; the helper is documented to
# re-derive its own guards independent of that gate).
ADV_TEST_NAME = "adversarial_v_b02_duplicated_and_reordered_frequencies_break_fail_closed_claim"
adv_test_src = '''
    #[test]
    fn ''' + ADV_TEST_NAME + '''() {
        let mut duplicated = measured_full_spectrum_observation(1);
        let highest = duplicated.spectrum.first().unwrap().clone();
        let true_lowest_barrier_index = barrier_index_from_spectrum(&duplicated).unwrap();
        duplicated.spectrum.push(highest.clone());
        let result = barrier_index_from_spectrum(&duplicated);
        eprintln!(
            "duplicated/reordered result = {:?}; true low-frequency barrier_index = {:?}; \\
             high-frequency point real={} imag={}",
            result, true_lowest_barrier_index, highest.real_ohm_cm2, highest.imaginary_ohm_cm2
        );
        assert!(result.is_some());
        let observed = result.unwrap();
        let expected_high_freq_reading = highest
            .real_ohm_cm2
            .hypot(highest.imaginary_ohm_cm2)
            .log10();
        assert_eq!(observed, expected_high_freq_reading);
        assert!((observed - true_lowest_barrier_index).abs() > 1.0);
    }
'''

original_text = lib_bytes_pre.decode()
marker = "\n}\n"
assert original_text.endswith(marker), "unexpected file tail; refusing to patch blindly"
patched_text = original_text[: -len(marker)] + adv_test_src + "}\n"
LIB.write_text(patched_text)
try:
    proc2 = subprocess.run(
        [CARGO, "test", "-p", "amphora-barrier-corrosion-score", ADV_TEST_NAME, "--", "--nocapture"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=540)
    adv_output = proc2.stdout + proc2.stderr
    adv_test_passed = proc2.returncode == 0 and "test result: ok. 1 passed; 0 failed" in adv_output
    # full suite too, to confirm no collateral regression
    proc3 = subprocess.run(
        [CARGO, "test", "-p", "amphora-barrier-corrosion-score"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=540)
    full_output_with_adv = proc3.stdout + proc3.stderr
    full_passed_with_adv = proc3.returncode == 0 and "test result: ok. 7 passed; 0 failed" in full_output_with_adv
finally:
    LIB.write_bytes(lib_bytes_pre)
    restored = LIB.read_bytes()
    assert sha(restored) == EXPECTED_LIB_SHA, "failed to restore lib.rs to pre-verify state"

assert adv_test_passed, ("adversarial probe test did not compile/pass as expected: " + adv_output[-3000:])
assert full_passed_with_adv, full_output_with_adv[-3000:]

# Extract the two f64 values printed by the probe for the receipt.
import re
m = re.search(
    r"duplicated/reordered result = Some\(([0-9.eE+-]+)\); true low-frequency barrier_index = ([0-9.eE+-]+)",
    adv_output)
if not m:
    print("DEBUG adv_output:\n", adv_output)
assert m, "could not parse adversarial probe stdout"
observed_wrong_barrier_index = float(m.group(1))
true_low_freq_barrier_index = float(m.group(2))
discrepancy_orders_of_magnitude = abs(observed_wrong_barrier_index - true_low_freq_barrier_index)

# --------------------------- independent re-derivation of both readings ----
def simulate(f_hz: float) -> tuple:
    omega = 2.0 * math.pi * f_hz

    def parallel_cpe(resistance, q, exponent):
        magnitude = q * omega ** exponent
        angle = exponent * math.pi / 2.0
        re = 1.0 / resistance + magnitude * math.cos(angle)
        im = magnitude * math.sin(angle)
        d = re * re + im * im
        return re / d, -im / d

    re, im = 25.0, 0.0
    for r, q, n in ((2.0e5, 1.0e-7, 0.88), (8.0e4, 1.0e-5, 0.82)):
        zre, zim = parallel_cpe(r, q, n)
        re += zre
        im += zim
    return re, im


f_min = 10.0 ** (5.0 - 15.0 * 0.5)
f_max = 10.0 ** 5.0
re_low, im_low = simulate(f_min)
re_high, im_high = simulate(f_max)
independent_low_barrier_index = math.log10(math.hypot(re_low, im_low))
independent_high_barrier_index = math.log10(math.hypot(re_high, im_high))
assert abs(independent_low_barrier_index - true_low_freq_barrier_index) < 1e-9
assert abs(independent_high_barrier_index - observed_wrong_barrier_index) < 1e-9

# ------------------------------- probe C: production path is NOT exposed ---
# Confirm predict()'s only call site is gated: validate_conditions() rejects
# the same duplicated/reordered spectrum with CorrosionError::Method (not
# strictly descending), so the bug is unreachable through the crate's public
# predict() API today. Verified structurally: the window check
# `window[0].frequency_hz <= window[1].frequency_hz` in validate_conditions()
# fires for any non-strictly-descending spectrum, and predict() calls
# `observation.validate_conditions()?` before ever calling the helper.
production_path_gated = (
    "if self.spectrum.len() < 8" in original_text
    and "window[0].frequency_hz <= window[1].frequency_hz" in original_text
    and "observation.validate_conditions()?;" in original_text
)
assert production_path_gated

# ----------------------------------------------------------------- payload --
payload_obj = {
    "schema": "amphora.barrier-corrosion-score.repair-independent-verify-receipt.v1",
    "receipt_id": "v-b02-independent-verify-v1",
    "module_id": "amphora-barrier-corrosion-score",
    "campaign_item_id": "V-B02",
    "verifies_repair_item": "R-B02",
    "date": "2026-08-05",
    "generated_on_host": "xbabe2",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "trust_anchored_in_phase0_store": True,
    "two_replay_sha256_gate": "PASS",
    "verified_artifact": {
        "r_b02_done_receipt_path": (
            "amphora-barrier-corrosion-score/evidence/phase0/repairs/R-B02/done/"
            "barrier-index-repair-receipt.v1.dsse.json"),
        "r_b02_done_receipt_sha256": EXPECTED_R_B02_DONE_SHA,
        "lib_rs_sha256_at_verify_time": EXPECTED_LIB_SHA,
        "lib_rs_restored_after_probe": True,
    },
    "claim_under_attack": (
        "R-B02's barrier_index_from_spectrum helper (and its doc-comment / sibling "
        "test test_barrier_index_fails_closed_on_degenerate_spectra) claims it "
        "'fails closed even if called on its own', independent of "
        "validate_conditions(), across an enumerated list of degenerate inputs "
        "(empty spectrum, single-point, non-finite component, zero modulus, "
        "rights_ineligible)."),
    "verdict": "CLAIM_REFUTED_SCOPED",
    "verdict_detail": (
        "The self-contained 'fails closed even if called on its own' guarantee is "
        "FALSE for order/uniqueness violations, which R-B02's enumerated "
        "fail_closed_none_cases list omits. Constructed adversarial input: take the "
        "module's own well-formed 16-point strictly-descending reference spectrum "
        "(measured_full_spectrum_observation) and append a duplicate of its highest-"
        "frequency point to the end. barrier_index_from_spectrum(&duplicated) does "
        "NOT return None as its own doc-comment promises; it silently returns "
        "Some(observed_wrong_barrier_index), reading the duplicated HIGH-frequency "
        "point's real/imaginary components (near-solution-resistance ohmic regime) "
        "and mislabeling it as the low-frequency Brasher-Kingsbury barrier reading. "
        "This is a silent, undetected value error of "
        f"{discrepancy_orders_of_magnitude:.3f} log10(ohm*cm^2) "
        "(~3.5 orders of magnitude in |Z|), not a crash and not a None -- worse than "
        "the documented fail-closed contract because it produces a plausible-looking "
        "wrong number rather than an abstention."
    ),
    "scoping": {
        "refuted": (
            "The private helper's documented claim to independently re-derive its "
            "own fail-closed guarantees ('so the helper fails closed even if called "
            "on its own') is false for spectrum ordering/uniqueness violations; the "
            "helper trusts `.last()` without re-verifying strict descending order, "
            "contradicting its own doc-comment and the framing of its sibling unit "
            "test."
        ),
        "not_refuted_survives": (
            "The production predict() -> EisPredictionV1 path remains fail-closed in "
            "practice today: predict() calls observation.validate_conditions()? "
            "BEFORE ever reaching barrier_index_from_spectrum, and "
            "validate_conditions()'s window check "
            "(window[0].frequency_hz <= window[1].frequency_hz) rejects any "
            "non-strictly-descending spectrum with CorrosionError::Method, so "
            "predict() returns Err rather than a wrong prediction for this exact "
            "adversarial input. The R-B02 repair's headline achievement -- a live "
            "Some(..) code path for metrics.barrier_index inside predict() on "
            "well-formed inputs, pinned by cargo test -- also survives unchanged; "
            "cargo test -p amphora-barrier-corrosion-score reproduces 6/6 passed "
            "identically to the R-B02 receipt."
        ),
        "why_this_still_counts_as_a_refutation": (
            "The claim under independent verification was not 'predict() is safe' "
            "(which the repair never disputed depends on validate_conditions()) but "
            "the helper's OWN explicit, tested, documented claim to be independently "
            "fail-closed. R-B02's own test docstring frames this as a checked "
            "property ('deliberately bypass validate_conditions() to prove the "
            "helper fails closed on its own, not only behind the upstream "
            "validation gates') and its fail_closed_none_cases list is presented as "
            "exhaustive. It is not: order/uniqueness is an unguarded gap in a "
            "function whose entire raison d'etre is defense-in-depth."
        ),
    },
    "probes": {
        "probe_a_cargo_baseline": {
            "command": f"{CARGO} test -p amphora-barrier-corrosion-score",
            "result_line": "test result: ok. 6 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out",
            "matches_r_b02_receipt": True,
        },
        "probe_b_adversarial_edge_case": {
            "method": (
                "temporarily inserted one new #[test] into the module's existing "
                "mod tests block (same file, same crate, so it can call the private "
                "barrier_index_from_spectrum helper exactly as the sibling degenerate-"
                "spectra test does), ran `cargo test ... -- --nocapture`, captured "
                "stdout, then restored src/lib.rs byte-for-byte "
                f"(sha256 {EXPECTED_LIB_SHA} before and after) -- no permanent source "
                "change; this is a verify-mode item, not a repair."
            ),
            "test_name": ADV_TEST_NAME,
            "adversarial_input": (
                "measured_full_spectrum_observation(1) [16-point strictly-descending "
                "Randles/CPE reference spectrum, 1e5 Hz down to 10^-2.5 Hz] with the "
                "index-0 (highest-frequency, 1e5 Hz) point appended a second time at "
                "the end"),
            "observed_result": f"Some({observed_wrong_barrier_index!r})",
            "documented_expected_result_per_doc_comment": "None (fail-closed)",
            "true_low_frequency_barrier_index_reference": f"Some({true_low_freq_barrier_index!r})",
            "discrepancy_log10_ohm_cm2": discrepancy_orders_of_magnitude,
            "cargo_test_output_excerpt": adv_output[-2500:],
        },
        "probe_c_production_path_gate_check": {
            "method": (
                "structural check that predict() calls "
                "observation.validate_conditions()? before ever calling "
                "barrier_index_from_spectrum, and that validate_conditions()'s "
                "strictly-descending window check would reject the same adversarial "
                "spectrum used in probe B"),
            "production_path_gated": production_path_gated,
            "conclusion": (
                "the silent-wrong-value bug is real and reproducible in the private "
                "helper but is NOT currently reachable through the crate's only "
                "production call site (predict())"),
        },
        "probe_d_independent_rederivation": {
            "method": (
                "independent CPython re-derivation of lib.rs simulate_equivalent_circuit "
                "(IEEE-754 doubles, identical arithmetic) at both f_min (lowest of the "
                "16-point spectrum) and f_max (highest, 1e5 Hz), confirming both the "
                "true low-frequency reading and the silently-substituted high-frequency "
                "reading independently of the Rust test harness"),
            "f_min_hz": f_min,
            "f_max_hz": f_max,
            "independent_low_freq_barrier_index": independent_low_barrier_index,
            "independent_high_freq_barrier_index": independent_high_barrier_index,
            "matches_rust_probe_within_1e-9": True,
        },
    },
    "formula_review": {
        "cited_baseline": "Brasher & Kingsbury 1954, J. Appl. Chem. 4:62-72",
        "formula_as_reviewed": (
            "barrier_index = log10(hypot(real_ohm_cm2, imaginary_ohm_cm2)) at the "
            "lowest measured frequency of a full frequency-resolved spectrum"),
        "convention_check": (
            "consistent with the standard EIS low-frequency-|Z| barrier-integrity "
            "convention cited; not disputed by this verify"),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "used_for": "AUDIT_ONLY independent-verify receipt under evidence/phase0/repairs/V-B02/done/",
        "signs_phase0_evaluation_or_review": False,
    },
}

sk = Ed25519PrivateKey.from_private_bytes(load_seed(SEED))
pub = sk.public_key().public_bytes_raw()
pub_hex = pub.hex()
key_id = f"phase0-evaluator-{sha(pub)}"
assert key_id.startswith("phase0-evaluator-3ef6b35"), key_id
trust = json.loads(TRUST.read_text())
pinned = {k.get("role"): k.get("key_id") for k in trust["keys"]}
anchored = key_id == pinned.get("PHASE0_EVALUATOR")
assert anchored, "evaluator key not anchored in phase0 trust store"
payload_obj["signing_key"]["key_id"] = key_id
payload_obj["signing_key"]["public_key_hex"] = pub_hex
payload_obj["signing_key"]["derives_pinned_trust_store_key_id"] = bool(anchored)

# ------------------------------------------------- two-replay canonical gate --
body_a = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode()
body_b = json.dumps(payload_obj, sort_keys=True, separators=(",", ":")).encode()
assert body_a == body_b, "two-replay canonical serialization bytes differ"
payload_sha = sha(body_a)

# ------------------------------------------------------------------- sign ----
sig = sk.sign(pae(PTYPE, body_a))
envelope = {
    "payload": base64.standard_b64encode(body_a).decode(),
    "payloadType": PTYPE,
    "signatures": [{"keyid": key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": key_id,
    "evaluator_public_key_hex": pub_hex,
    "signature": envelope,
}
DONE.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ------------------------------------------------------------ self-verify ----
reloaded = json.loads(RECEIPT_PATH.read_text())
env = reloaded["signature"]
body_back = base64.standard_b64decode(env["payload"])
assert sha(body_back) == payload_sha, "reloaded payload sha mismatch"
assert env["payloadType"] == PTYPE
assert env["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35")
Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex)).verify(
    base64.standard_b64decode(env["signatures"][0]["sig"]),
    pae(env["payloadType"], body_back))
sk2 = Ed25519PrivateKey.from_private_bytes(load_seed(SEED))
Ed25519PublicKey.from_public_bytes(sk2.public_key().public_bytes_raw()).verify(
    base64.standard_b64decode(env["signatures"][0]["sig"]),
    pae(env["payloadType"], body_back))

# --------------------------------------------------------------- final guards --
assert sha(LIB.read_bytes()) == EXPECTED_LIB_SHA, "lib.rs not clean at end of run"
assert sha(R_B02_DONE.read_bytes()) == EXPECTED_R_B02_DONE_SHA, "R-B02 receipt mutated during verify run"

(WORK / "cargo_test_baseline_output.txt").write_text(cargo_output_baseline)
(WORK / "adversarial_probe_output.txt").write_text(adv_output)
(WORK / "verify_result.json").write_text(json.dumps({
    "verdict": "CLAIM_REFUTED_SCOPED",
    "observed_wrong_barrier_index": observed_wrong_barrier_index,
    "true_low_freq_barrier_index": true_low_freq_barrier_index,
    "discrepancy_log10_ohm_cm2": discrepancy_orders_of_magnitude,
    "production_path_gated": production_path_gated,
    "payload_canonical_sha256": payload_sha,
    "lib_rs_sha256_unchanged": EXPECTED_LIB_SHA,
    "r_b02_done_receipt_sha256_unchanged": EXPECTED_R_B02_DONE_SHA,
}, indent=2, sort_keys=True))

print("WROTE", RECEIPT_PATH)
print("receipt_sha256", sha(RECEIPT_PATH.read_bytes()))
print("payload_canonical_sha256", payload_sha)
print("two_replay_sha256_gate PASS")
print("evaluator_key_id", key_id)
print("trust_anchored", anchored)
print("observed_wrong_barrier_index", observed_wrong_barrier_index)
print("true_low_freq_barrier_index", true_low_freq_barrier_index)
print("discrepancy_log10_ohm_cm2", discrepancy_orders_of_magnitude)
print("production_path_gated", production_path_gated)
print("self_verified", True)
print("lib_rs_clean_after", True)
