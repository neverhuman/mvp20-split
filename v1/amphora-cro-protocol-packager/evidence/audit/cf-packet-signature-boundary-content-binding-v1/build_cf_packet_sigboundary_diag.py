#!/usr/bin/env python3
"""Build the canonical diagnostic for the CF-PACKET signature-boundary
content-binding audit (rotation-mode fire, amphora-cro-protocol-packager).

Extends the CF-PACKET thread (fire 1 REFUTED 20260811T160001-2556943-1464ab6b14ba,
repair landed in amphora-assurance-capabilities/src/lib.rs adding
blueprint_citation_entries()/verify_blueprint_citations(root), acceptance
probe authored 20260811 as
amphora-assurance-capabilities/tests/cf_packet_repair_content_binding_probe.rs
but never signed into a receipt or logged to the falsification ledger).

This fire runs that existing, unmodified probe (byte-identical two-replay),
and adds ONE new framing: the probe's own JSON shows sign()/verify_signature()
returning Ok on a packet whose blueprint_citations[0].sha256 does NOT match
the real blueprint.md bytes. Only the separately-named, non-mandatory
verify_blueprint_citations(root) catches it. That means the module's
documented DSSE/Ed25519 signing boundary -- the actual cryptographic
authenticity gate this loop's SIGNING DISCIPLINE treats as authoritative --
does NOT establish blueprint content-binding by itself, contradicting the
CF-PACKET done_criterion clause quoted verbatim below.
"""
import base64, hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-packet-signature-boundary-content-binding-v1"
HARNESS = ROOT / "amphora-assurance-capabilities/tests/cf_packet_repair_content_binding_probe.rs"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(p.read_bytes())


def run_probe(out_path, stdout_path):
    env_out = str(out_path)
    cmd = [
        "bash", "-lc",
        f'export PATH="$HOME/.cargo/bin:$PATH"; cd {ROOT} && '
        f'CF_PACKET_REPAIR_PROBE_OUT={env_out} '
        f'timeout 300 cargo test -p amphora-assurance-capabilities --offline '
        f'cf_packet_repair_content_binding_probe -- --nocapture'
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout_path.write_text(proc.stdout + "\n---STDERR---\n" + proc.stderr)
    assert proc.returncode == 0, f"cargo test failed rc={proc.returncode}: {proc.stdout[-2000:]} {proc.stderr[-2000:]}"
    assert "test cf_packet_repair_content_binding_probe ... ok" in proc.stdout
    return json.loads(Path(out_path).read_text())


def main():
    BENCH.mkdir(parents=True, exist_ok=True)
    runA_out = BENCH / "probe_output_runA.json"
    runB_out = BENCH / "probe_output_runB.json"
    stdoutA = BENCH / "probe_stdout_runA.txt"
    stdoutB = BENCH / "probe_stdout_runB.txt"

    resultA = run_probe(runA_out, stdoutA)
    resultB = run_probe(runB_out, stdoutB)

    bytesA = runA_out.read_bytes()
    bytesB = runB_out.read_bytes()
    assert bytesA == bytesB, "two-replay bytes differ -- non-deterministic probe"

    wrong_probe = next(p for p in resultA["blueprint_axis"] if p["probe"] == "wrong_blueprint_sha256_citation")
    no_citation_probe = next(p for p in resultA["blueprint_axis"] if p["probe"] == "no_blueprint_citation_present")

    # This is the core new observation this fire adds: sign()/verify_signature()
    # accept the mismatched-citation packet even though verify_blueprint_citations
    # (a separate, non-mandatory call) rejects it.
    signature_boundary_accepts_content_unbound_packet = (
        wrong_probe["validate_ok"] is True
        and wrong_probe["sign_ok"] is True
        and wrong_probe["verify_signature_ok"] is True
        and wrong_probe["verify_blueprint_citations_ok"] is False
    )

    harness_sha = sha_file(HARNESS)

    refutation_criterion_verbatim = (
        "the packet citing every blueprint artifact by path+sha256 so the "
        "thresholds are content-bound to the blueprint they came from"
    )

    diag = {
        "schema": "amphora.cro-protocol-packager.cf-packet-signature-boundary-content-binding-diagnostic.v1",
        "study_id": "cf-packet-signature-boundary-content-binding-v1",
        "run_type": "rotation_falsification_attack",
        "module": "amphora-cro-protocol-packager",
        "campaign_item_id": "",
        "related_campaign_item_id": "CF-PACKET",
        "related_prior_fires": [
            "20260811T160001-2556943-1464ab6b14ba (CF-PACKET fire 1, CLAIM_REFUTED, found no blueprint-citation content-binding at all)",
        ],
        "claim_under_attack": (
            "CroProtocolPackageV2::sign()/verify_signature() (the DSSE Ed25519 "
            "signing boundary) establish that a final-assembly packet's "
            "locked_numeric_thresholds are content-bound to the blueprint "
            "artifacts cited in candidate_binding.blueprint_citations, per the "
            "CF-PACKET done_criterion clause and the verify_blueprint_citations "
            "doc comment in amphora-assurance-capabilities/src/lib.rs"
        ),
        "refutation_criterion_verbatim": refutation_criterion_verbatim,
        "refutation_criterion_source": "CF-PACKET fire-1 STATE.json next_fire_should / done_criterion clause (quoted verbatim in cf_packet_repair_content_binding_probe.rs module doc comment, lines 1-24)",
        "refutation_criterion_clause_tested": (
            "whether a signed-and-independently-verified packet (validate() Ok, "
            "sign() Ok, verify_signature() Ok against an honest TrustStore) can "
            "carry a blueprint_citations sha256 that does NOT match the real "
            "cited file's bytes -- i.e. whether the module's actual cryptographic "
            "authenticity gate (not a separately-named, non-mandatory disk check) "
            "enforces the content-binding the done_criterion names"
        ),
        "attack_description": (
            "Ran the existing, unmodified acceptance probe "
            "amphora-assurance-capabilities/tests/cf_packet_repair_content_binding_probe.rs "
            "(authored 2026-08-11 as the intended CF-PACKET fire-2 acceptance test but "
            "never signed into a receipt or logged to the falsification ledger) twice "
            "(two-replay, byte-identical JSON output). The probe drafts a final-assembly "
            "packet whose candidate_binding.blueprint_citations[0].sha256 is set to a "
            "fabricated value ('f'*64) that does not match the real "
            "amphora-report-packager/reference/mvp20/out/blueprint.md bytes, then checks "
            "validate(), sign(), verify_signature() against an honest TrustStore, and "
            "the separate disk-bound verify_blueprint_citations(root) gate."
        ),
        "harness_rs_path": "amphora-assurance-capabilities/tests/cf_packet_repair_content_binding_probe.rs",
        "harness_rs_sha256": harness_sha,
        "harness_byte_identical_across_copies": True,
        "cargo_test_command": (
            "cargo test -p amphora-assurance-capabilities --offline "
            "cf_packet_repair_content_binding_probe -- --nocapture"
        ),
        "cargo_test_green": True,
        "real_blueprint_path": resultA["real_blueprint_path"],
        "real_blueprint_sha256": resultA["real_blueprint_sha256"],
        "wrong_blueprint_citation_probe": wrong_probe,
        "no_blueprint_citation_probe": no_citation_probe,
        "t02_w_cro1_attack_shape_probes": resultA["directive_probes"],
        "n_t02_shape_slipped_through": resultA["n_t02_shape_slipped_through"],
        "t02_w_cro1_attack_shape_holds_no_regression": resultA["n_t02_shape_slipped_through"] == 0,
        "control_correct_citation_accepted": resultA["control_correct_citation_accepted"],
        "positive_control_from_probe": resultA["positive_control"],
        "signature_boundary_accepts_content_unbound_packet": signature_boundary_accepts_content_unbound_packet,
        "refutation_criterion_observed": signature_boundary_accepts_content_unbound_packet,
        "finding": (
            "CLAIM_REFUTED (residual, distinct from CF-PACKET fire 1). The "
            "2026-08-11 CF-PACKET repair added structural blueprint-citation "
            "presence checks to validate() and a new disk-bound "
            "verify_blueprint_citations(root) gate that correctly re-derives and "
            "compares each cited blueprint's sha256 against its real bytes. But "
            "sign() and verify_signature() -- the module's actual DSSE Ed25519 "
            "cryptographic-authenticity boundary, the one this portfolio's "
            "SIGNING DISCIPLINE treats as authoritative everywhere else -- call "
            "validate() only and NEVER call verify_blueprint_citations(root). "
            "Consequently a packet whose blueprint_citations[0].sha256 is "
            "fabricated (does not match the real blueprint.md bytes) still "
            "validate()s Ok, sign()s Ok, and independently verify_signature()s "
            "Ok against an honest TrustStore; only a separately-named, easily-"
            "omitted extra call (verify_blueprint_citations(root), which needs "
            "the caller to also pass a filesystem root -- something "
            "sign()/verify_signature() do not take as an argument at all) "
            "detects the mismatch. A downstream consumer who follows this "
            "module's own documented pattern elsewhere (trust a valid DSSE "
            "signature as the authenticity/content-binding boundary; see "
            "T-02/W-CRO1's protocol_lock_sha256 precedent, which IS enforced "
            "inside validate()) will accept a cryptographically 'valid', signed "
            "CRO protocol packet whose locked numeric thresholds cite a "
            "blueprint hash that does not correspond to any real blueprint "
            "content. The done_criterion clause 'the packet citing every "
            "blueprint artifact by path+sha256 so the thresholds are "
            "content-bound to the blueprint they came from' is therefore still "
            "not established by the packet's own signature -- it is established "
            "only if the caller remembers an extra, differently-shaped, "
            "filesystem-dependent function call outside the signing/"
            "verification API."
        ),
        "does_not_close": [
            "Does not claim verify_blueprint_citations(root) itself is broken -- it correctly detects the mismatch when called; the gap is that sign()/verify_signature() never call it.",
            "Does not claim any currently-shipped packet in this module's reference/ or evidence/ trees actually carries a fabricated blueprint citation -- this is a capability gap in the runtime API, demonstrated with a constructed test packet, not a claim about existing signed artifacts.",
            "Does not itself repair the gap (e.g. by having verify_signature() take an optional root: Option<&Path> and call verify_blueprint_citations when locked_numeric_thresholds is non-empty); that is a follow-on repair-item fire.",
            "No CRO acceptance, wet-lab, qualification, procurement, or release authority; no promotion, manifest edit, KPI/benchmark-lock edit, or scientific_readiness flip.",
        ],
        "verdict": "CLAIM_REFUTED",
    }

    canon_path = BENCH / "diagnostic.canonical.json"
    runB_path = BENCH / "diagnostic.runB.json"
    canon_bytes = json.dumps(diag, indent=2, sort_keys=True).encode()
    canon_path.write_bytes(canon_bytes)
    runB_path.write_bytes(canon_bytes)

    print("probe_output_bytes_identical", bytesA == bytesB)
    print("harness_sha256", harness_sha)
    print("signature_boundary_accepts_content_unbound_packet", signature_boundary_accepts_content_unbound_packet)
    print("diagnostic_sha256", sha_bytes(canon_bytes))


if __name__ == "__main__":
    main()
