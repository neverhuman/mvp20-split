#!/usr/bin/env python3
"""remote_verify.py — runs ON xbabe2, prints one JSON object to stdout.

Invoked as:  python3 - <base64-json-params>      (script itself arrives on stdin)
All params travel as ONE base64 token, so no value is ever re-parsed by a
shell. This closes the v2 `ssh bash -s "$TARGET"` injection.

Modes:
  snapshot : {path: sha256} for the target module + current ledger line count
  verify   : content set-diff vs that snapshot, real Ed25519 DSSE verification,
             and a fire-id-bound ledger check

Every verification is identity-bound:
  * artifacts are found by CONTENT HASH set-diff against the pre-fire snapshot
    (never mtime) and intersected with what the agent DECLARED, so a bystander
    agent's writes cannot be credited and `touch` cannot manufacture evidence
  * receipts are verified by real Ed25519 over the DSSE PAE encoding against
    the pinned Phase-0 key — not `jq '.signature|type' == "object"`
  * the ledger must contain a line carrying THIS fire's fire_id
check=="OK" only when every step completed; any exception -> check=="FAILED"
plus non-zero exit, so the caller fails closed.
"""
import base64
import hashlib
import json
import os
import sys
import traceback

DEFAULT_SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
SKIP_DIRS = {"target", ".git", "__pycache__", "node_modules", ".venv"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan_module(root, module):
    """Content-hash every candidate evidence JSON in ONE module.
    Regular files only — symlinks are skipped so they cannot fabricate
    an 'artifact' that points at some pre-existing signed receipt."""
    out = {}
    base = os.path.join(root, module)
    for sub in ("evidence", "benchmarks", os.path.join("reference", "mvp20", "data")):
        top = os.path.join(base, sub)
        if not os.path.isdir(top):
            continue
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not fn.endswith(".json"):
                    continue
                p = os.path.join(dirpath, fn)
                if os.path.islink(p) or not os.path.isfile(p):
                    continue
                try:
                    out[os.path.relpath(p, root)] = sha256_file(p)
                except OSError:
                    pass
    return out


def count_lines(path):
    n = 0
    if path and os.path.isfile(path):
        with open(path, "r", errors="replace") as fh:
            for _ in fh:
                n += 1
    return n


def pae(payload_type, payload):
    """DSSE Pre-Authentication Encoding — identical construction to the
    in-tree sign_*.py scripts, which verify immediately after signing."""
    return b"DSSEv1 %d %s %d %s" % (
        len(payload_type), payload_type.encode(), len(payload), payload
    )


def load_verifier(seed_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    if not os.path.isabs(seed_path):
        raise ValueError("signing key path must be absolute")
    with open(seed_path, "rb") as fh:
        seed = fh.read()
    if len(seed) != 32:
        raise ValueError("unexpected Phase-0 seed length %d" % len(seed))
    return Ed25519PrivateKey.from_private_bytes(seed).public_key()


def verify_dsse(path, pubkey):
    """True iff this file is a DSSE envelope whose signature verifies under the
    pinned Phase-0 key. Accepts the envelope at top level or nested under
    .signature — both conventions exist in-tree."""
    from cryptography.exceptions import InvalidSignature
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return False, "unreadable"
    if not isinstance(doc, dict):
        return False, "not-object"
    env = doc
    if "payload" not in env and isinstance(env.get("signature"), dict):
        env = env["signature"]
    ptype = env.get("payloadType")
    payload_b64 = env.get("payload")
    sigs = env.get("signatures")
    if not (isinstance(ptype, str) and isinstance(payload_b64, str)
            and isinstance(sigs, list) and sigs):
        return False, "not-dsse-envelope"
    try:
        payload = base64.standard_b64decode(payload_b64)
    except Exception:
        return False, "bad-payload-b64"
    for s in sigs:
        if not isinstance(s, dict) or not isinstance(s.get("sig"), str):
            continue
        try:
            pubkey.verify(base64.standard_b64decode(s["sig"]), pae(ptype, payload))
            return True, "ed25519-ok"
        except InvalidSignature:
            continue
        except Exception:
            continue
    return False, "signature-invalid"



def payload_of(path):
    """Decode a DSSE receipt's payload. The verifier has until now checked only
    that a receipt is signed -- never what it claims. W-RTA2 proved that lets a
    deliberately weak attack license a CLAIM_SURVIVED."""
    try:
        d = json.load(open(path))
    except Exception:
        return None
    env = d if "payload" in d else (d.get("signature") if isinstance(d.get("signature"), dict) else None)
    if not isinstance(env, dict) or "payload" not in env:
        return None
    try:
        return json.loads(base64.b64decode(env["payload"]))
    except Exception:
        return None


def find_positive_control(obj, depth=0):
    """Locate a positive_control block anywhere in a receipt payload.
    Contract: it names a defect deliberately planted in the attack's own input,
    and records whether the attack DETECTED it. An attack that cannot catch a
    known-planted defect is too weak to license a survival."""
    if depth > 8:
        return None
    if isinstance(obj, dict):
        pc = obj.get("positive_control")
        if isinstance(pc, dict):
            return pc
        for v in obj.values():
            r = find_positive_control(v, depth + 1)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj[:24]:
            r = find_positive_control(v, depth + 1)
            if r:
                return r
    return None


def _norm(text):
    """Collapse whitespace and case so a verbatim restatement still matches after
    line-wrapping or re-indentation inside a JSON payload."""
    return " ".join(str(text or "").split()).lower()


def directive_citation_verdict(root, credited, directive_ref, refutation_criterion):
    """Is this fire's receipt actually bound to the founder obligation it served?

    The prompt requires a receipt to carry directive_path + directive_sha256 +
    directive_obligation, and to restate the obligation's pre-committed
    refutation_criterion verbatim. Until now that was enforced by prose alone --
    the same defect W-RTA2 proved for the survival bar, reintroduced by the very
    change meant to apply its lesson.

    Matching is on VALUES, not key names. Reviewing T-01 by hand I searched for a
    literal `refutation_criterion` key and wrongly reported it absent; that receipt
    had carried it across refutation_criterion_verbatim/_observed/_statement. A
    checker keyed on field names would repeat my mistake, so this searches the
    decoded payload for the document hash, the obligation id and the founder's own
    sentence.
    """
    ref = directive_ref or {}
    if not ref.get("item_id"):
        return {"required": False, "ok": True, "reason": "item-carries-no-directive_ref"}

    want_sha = str(ref.get("md_sha256") or "")
    want_obl = str(ref.get("item_id") or "")
    want_path = str(ref.get("md_path") or "")
    want_refut = _norm(refutation_criterion)

    decoded, best = 0, None
    for rel in credited:
        payload = payload_of(os.path.join(root, rel))
        if payload is None:
            continue
        decoded += 1
        nblob = _norm(json.dumps(payload, ensure_ascii=False))
        missing = []
        if want_sha and want_sha.lower() not in nblob:
            missing.append("directive_sha256")
        if want_obl and _norm(want_obl) not in nblob:
            missing.append("directive_obligation")
        if want_path and _norm(want_path) not in nblob:
            missing.append("directive_path")
        if want_refut and want_refut not in nblob:
            missing.append("refutation_criterion-restated-verbatim")
        if not missing:
            return {"required": True, "ok": True, "receipt": rel, "decoded": decoded,
                    "obligation": want_obl}
        if best is None or len(missing) < len(best[1]):
            best = (rel, missing)

    if decoded == 0:
        return {"required": True, "ok": False, "decoded": 0,
                "reason": "could-not-decode-any-credited-receipt-payload -- this is a VERIFIER "
                          "defect or an unknown envelope shape, not evidence about the fire"}
    return {"required": True, "ok": False, "decoded": decoded, "receipt": best[0],
            "obligation": want_obl, "missing": best[1],
            "reason": "credited receipt does not cite the founder obligation it served: missing "
                      + ", ".join(best[1])}


def positive_control_verdict(root, credited, outcome):
    """Only CLAIM_SURVIVED is gated. Refutations carry their own evidence, and
    gating them would stall repair work."""
    if (outcome or "").strip() != "CLAIM_SURVIVED":
        return {"required": False, "ok": True, "reason": "not-a-survival"}
    decoded = 0
    for rel in credited:
        pl = payload_of(os.path.join(root, rel))
        if pl is None:
            continue
        decoded += 1
        pc = find_positive_control(pl)
        if not pc:
            continue
        detected = pc.get("detected")
        if detected is None:
            detected = pc.get("attack_fired_on_planted_defect")
        if detected is True:
            return {"required": True, "ok": True, "receipt": rel, "decoded": decoded,
                    "planted": str(pc.get("planted_defect") or pc.get("mutation") or "")[:200]}
        return {"required": True, "ok": False, "receipt": rel, "decoded": decoded,
                "reason": "positive-control-present-but-attack-did-not-detect-the-planted-defect",
                "planted": str(pc.get("planted_defect") or pc.get("mutation") or "")[:200]}
    # Distinguish "decoded receipts, none carried a control" (a fact about the
    # attack) from "decoded nothing" (a fact about THIS verifier). Collapsing the
    # two would let an envelope-shape regression silently reject every survival
    # while looking exactly like an honest absence.
    if decoded == 0:
        return {"required": True, "ok": False, "decoded": 0,
                "reason": "could-not-decode-any-credited-receipt-payload -- this is a VERIFIER "
                          "defect or an unknown envelope shape, not evidence about the attack"}
    return {"required": True, "ok": False, "decoded": decoded,
            "reason": "no-positive-control-in-any-credited-receipt"}


def main():
    params = json.loads(base64.b64decode(sys.argv[1]))
    root = params["root"]
    module = params["module"]
    mode = params.get("mode", "verify")
    seed_path = params.get("signing_key_path") or DEFAULT_SEED_PATH

    if mode == "snapshot":
        print(json.dumps({
            "check": "OK",
            "snapshot": scan_module(root, module),
            "ledger_lines": count_lines(params.get("ledger_path", "")),
        }))
        return

    # ---- structured done_check: a glob that must match >=1 VERIFIED receipt --
    # Replaces v2's arbitrary shell string (which was remote code execution)
    # and v2's treatment of "no check defined" as a pass.
    if mode == "donecheck":
        import glob as _glob
        pat = params.get("glob") or ""
        if not pat:
            print(json.dumps({"check": "OK", "pass": False, "reason": "empty-glob"}))
            return
        pubkey = load_verifier(seed_path)
        matches = [p for p in _glob.glob(os.path.join(root, pat), recursive=True)
                   if os.path.isfile(p) and not os.path.islink(p)]
        for p in sorted(matches):
            ok, _ = verify_dsse(p, pubkey)
            if ok:
                print(json.dumps({"check": "OK", "pass": True,
                                  "matched": os.path.relpath(p, root)}))
                return
        print(json.dumps({"check": "OK", "pass": False,
                          "reason": "no-verified-receipt-matched",
                          "candidates": len(matches)}))
        return

    fire_id = params["fire_id"]
    ledger = params["ledger_path"]
    pre = params.get("pre_snapshot") or {}
    declared = set(params.get("declared_artifacts") or [])

    result = {
        "check": "FAILED", "verified_new_signed": 0,
        "signing_violations_in_module": 0, "ledger_has_fire_id": False,
        "ledger_lines": 0, "credited": [], "rejected": [], "notes": "",
    }

    post = scan_module(root, module)
    changed = [p for p, h in post.items() if pre.get(p) != h]

    # normalise declared artifact paths to repo-relative
    decl_rel = set()
    for d in declared:
        d = (d or "").strip()
        if not d:
            continue
        if d.startswith(root):
            d = os.path.relpath(d, root)
        decl_rel.add(d.lstrip("./"))

    pubkey = load_verifier(seed_path)

    credited, rejected = [], []
    for rel in sorted(changed):
        ok, why = verify_dsse(os.path.join(root, rel), pubkey)
        if not ok:
            # A changed, unsigned evidence file is charged to THIS fire only if
            # the agent actually claimed it. Otherwise it is a bystander write.
            if rel in decl_rel:
                rejected.append({"path": rel, "reason": why})
                result["signing_violations_in_module"] += 1
            continue
        if rel not in decl_rel:
            # Signed but undeclared -> almost certainly a concurrent writer.
            # Neither credit nor blame this fire for it.
            rejected.append({"path": rel, "reason": "signed-but-undeclared"})
            continue
        credited.append(rel)

    result["verified_new_signed"] = len(credited)
    result["credited"] = credited[:20]
    result["rejected"] = rejected[:20]

    lines, found = 0, False
    if os.path.isfile(ledger):
        with open(ledger, "r", errors="replace") as fh:
            for line in fh:
                lines += 1
                if fire_id and fire_id in line:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    if rec.get("fire_id") == fire_id and rec.get("module") == module:
                        found = True
    result["ledger_lines"] = lines
    result["ledger_has_fire_id"] = found
    result["check"] = "OK"
    result["positive_control"] = positive_control_verdict(
        root, result.get("credited") or [], params.get("outcome"))
    result["directive_citation"] = directive_citation_verdict(
        root, result.get("credited") or [], params.get("directive_ref") or {},
        params.get("refutation_criterion") or "")
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({
            "check": "FAILED", "verified_new_signed": 0,
            "signing_violations_in_module": 0, "ledger_has_fire_id": False,
            "ledger_lines": 0, "credited": [], "rejected": [], "snapshot": {},
            "notes": traceback.format_exc()[-400:],
        }))
        sys.exit(1)
