#!/usr/bin/env python3
"""Independent canonicalization-conformance audit for amphora-cro-protocol-packager.

Falsifiable hypothesis under test (a NEW axis, distinct from packet-binding-parity-v1
which cross-checked hash/rendering/signature *self-consistency*): the module's
candidate/formula SHA-256 binding canonicalization is byte-equal to RFC 8785 (JSON
Canonicalization Scheme, Rundgren/Jordan/Erdtman, June 2020), whose number
serialization is ECMA-262 (ECMAScript) 7.1.12.1 Number::toString.

We implement a TRUE RFC-8785 JCS serializer from the published algorithm (proper
ECMA-262 shortest-number rendering + UTF-16-code-unit key ordering + JCS string
escaping), validate its number path against a known-answer vector table, then apply
it to the shipped fixture and compare digests against the module's actual scheme
(the packet-binding harness' `json.dumps(...,separators,sort_keys)`).

AUDIT_ONLY. No runtime call, no promotion, no manifest/KPI/benchmark-lock edit.

Primary sources:
  - IETF RFC 8785 (2020) JSON Canonicalization Scheme (JCS).
  - ECMA-262 7.1.12.1 Number::toString (shortest round-tripping decimal).
  - NIST FIPS 180-4 (2015) SHA-256.
"""
import base64, hashlib, json, copy, sys
from decimal import Decimal
from pathlib import Path
from itertools import permutations

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FX = ROOT / "amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()

# ---- module's ACTUAL binding scheme (what run_binding_parity.py / runtime use) ----
def py_scheme(o): return json.dumps(o, separators=(",", ":"), sort_keys=True).encode()

# ---- TRUE RFC 8785 JCS -------------------------------------------------------------
def ecma262_number(x):
    """ECMA-262 7.1.12.1 Number::toString for a finite JSON number."""
    if isinstance(x, bool):
        raise TypeError("bool is not a number")
    if isinstance(x, int):
        return str(x)  # exact integers render directly (no float rounding)
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("non-finite number not permitted in JSON")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    d = Decimal(repr(abs(x)))            # repr() = shortest round-tripping decimal
    _, digits, exp = d.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:   # minimal significand s
        digits.pop(); exp += 1
    s = "".join(map(str, digits)); k = len(s); n = exp + k
    if k <= n <= 21:
        return sign + s + "0" * (n - k)
    if 0 < n <= 21:
        return sign + s[:n] + "." + s[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + s
    e = n - 1; es = "+" if e >= 0 else "-"
    body = s if k == 1 else s[0] + "." + s[1:]
    return sign + body + "e" + es + str(abs(e))

def jcs_str(s):
    out = ['"']
    for ch in s:
        c = ord(ch)
        if ch == '"': out.append('\\"')
        elif ch == '\\': out.append('\\\\')
        elif c == 0x08: out.append('\\b')
        elif c == 0x09: out.append('\\t')
        elif c == 0x0a: out.append('\\n')
        elif c == 0x0c: out.append('\\f')
        elif c == 0x0d: out.append('\\r')
        elif c < 0x20: out.append('\\u%04x' % c)
        else: out.append(ch)
    out.append('"')
    return "".join(out)

def jcs(o):
    if o is None: return "null"
    if o is True: return "true"
    if o is False: return "false"
    if isinstance(o, str): return jcs_str(o)
    if isinstance(o, bool): return "true" if o else "false"
    if isinstance(o, int): return str(o)
    if isinstance(o, float): return ecma262_number(o)
    if isinstance(o, list): return "[" + ",".join(jcs(v) for v in o) + "]"
    if isinstance(o, dict):
        items = sorted(o.items(), key=lambda kv: kv[0].encode("utf-16-be"))
        return "{" + ",".join(jcs_str(k) + ":" + jcs(v) for k, v in items) + "}"
    raise TypeError(f"unserializable: {type(o)}")

def jcs_bytes(o): return jcs(o).encode("utf-8")

def run():
    fx = json.loads(FX.read_bytes())
    p = fx["payload"]
    gates = {}

    # G1: ECMA-262 number KAT (theory anchor for the JCS number path)
    KAT = [
        (0.0, "0"), (1.0, "1"), (110.0, "110"), (40.0, "40"), (0.5, "0.5"),
        (0.2, "0.2"), (100.0, "100"), (0.002, "0.002"), (1e21, "1e+21"),
        (1e20, "100000000000000000000"), (1e-6, "0.000001"), (1e-7, "1e-7"),
        (1e30, "1e+30"), (-5.5, "-5.5"), (123.456, "123.456"),
        (9007199254740992.0, "9007199254740992"),
    ]
    kat_rows = []
    for val, exp in KAT:
        got = ecma262_number(val)
        kat_rows.append({"input_repr": repr(val), "expected": exp, "got": got,
                         "ok": got == exp})
    gates["G1_ecma262_number_kat"] = {
        "passed": all(r["ok"] for r in kat_rows),
        "n": len(kat_rows), "n_ok": sum(r["ok"] for r in kat_rows),
        "source": "ECMA-262 7.1.12.1 Number::toString / RFC 8785 3.2.2.3",
        "vectors": kat_rows,
    }

    # G2: candidate binding IS RFC-8785 conformant (all-string object -> digests agree)
    cand_py = sha(py_scheme(p["candidate"]))
    cand_jcs = sha(jcs_bytes(p["candidate"]))
    gates["G2_candidate_binding_jcs_conformant"] = {
        "passed": cand_py == cand_jcs == p["candidate_sha256"],
        "shipped": p["candidate_sha256"], "module_scheme": cand_py, "true_jcs": cand_jcs,
        "note": "candidate carries only strings/objects; module json.dumps and true JCS "
                "coincide, so the candidate binding is genuinely RFC-8785-conformant.",
    }

    # G3: formula binding DIVERGES from RFC-8785 JCS (integer-valued floats)
    form_py_bytes = py_scheme(p["recipe_steps"])
    form_jcs_b = jcs_bytes(p["recipe_steps"])
    form_py = sha(form_py_bytes); form_jcs = sha(form_jcs_b)
    # locate the divergence token
    diverging = sorted({f"{v:g}->json'{json.dumps(v)}'/jcs'{ecma262_number(v)}'"
                        for s in p["recipe_steps"] for v in [s["amount"]]
                        if json.dumps(v) != ecma262_number(v)})
    gates["G3_formula_binding_diverges_from_jcs"] = {
        "passed": (form_py == p["formula_sha256"]) and (form_jcs != p["formula_sha256"]),
        "shipped_formula_sha256": p["formula_sha256"],
        "module_scheme_sha256": form_py,
        "true_jcs_sha256": form_jcs,
        "divergence_class": "integer_valued_float_number_rendering",
        "diverging_tokens": diverging,
        "note": "module renders amount 110.0 as \"110.0\"; RFC-8785 JCS (ECMA-262) renders "
                "\"110\". The shipped formula_sha256 therefore is NOT the RFC-8785 JCS digest; "
                "it is a fixed Python-json compact-sorted digest. The 'RFC 8785 JCS' label on "
                "the formula binding overstates conformance.",
    }

    # G4: residual int/float ambiguity under module scheme; true JCS removes it.
    # Physically identical recipe: amount encoded as int 110 vs float 110.0.
    r_float = copy.deepcopy(p["recipe_steps"])           # amounts are floats (as shipped)
    r_int = copy.deepcopy(p["recipe_steps"])
    for s in r_int:
        if float(s["amount"]).is_integer():
            s["amount"] = int(s["amount"])               # semantically-equal integer encoding
    module_float = sha(py_scheme(r_float)); module_int = sha(py_scheme(r_int))
    jcs_float = sha(jcs_bytes(r_float)); jcs_int = sha(jcs_bytes(r_int))
    gates["G4_numeric_type_ambiguity"] = {
        # claim: the module scheme is AMBIGUOUS (two digests) while true JCS is not (one digest)
        "passed": (module_float != module_int) and (jcs_float == jcs_int),
        "module_scheme_int_encoding_sha256": module_int,
        "module_scheme_float_encoding_sha256": module_float,
        "module_scheme_ambiguous": module_float != module_int,
        "true_jcs_int_encoding_sha256": jcs_int,
        "true_jcs_float_encoding_sha256": jcs_float,
        "true_jcs_resolves_ambiguity": jcs_float == jcs_int,
        "note": "A producer that emits the 110 g mass as JSON integer 110 rather than float "
                "110.0 binds to a DIFFERENT formula_sha256 under the module scheme -- a real "
                "residual ambiguity in a binding whose stated purpose is to prevent ambiguous "
                "packets. Adopting the RFC-8785 JCS the receipt already claims would eliminate it.",
    }

    # G5: structural invariance -- canonicalization already defeats key-order/whitespace ambiguity
    def reserialize_variants(obj, n=6):
        """Produce byte-different but semantically-equal JSON encodings and reload."""
        variants = []
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for perm in list(permutations(keys))[:n]:
                d = {k: obj[k] for k in perm}
                for indent in (None, 2, 4):
                    variants.append(json.loads(json.dumps(d, indent=indent)))
        else:
            for indent in (None, 1, 2, 4):
                variants.append(json.loads(json.dumps(obj, indent=indent)))
        return variants
    cand_digests = {sha(jcs_bytes(v)) for v in reserialize_variants(p["candidate"])}
    step_digests = {sha(jcs_bytes(v)) for v in reserialize_variants(p["recipe_steps"][0])}
    gates["G5_structural_invariance"] = {
        "passed": len(cand_digests) == 1 and len(step_digests) == 1,
        "candidate_distinct_digests_over_reencodings": len(cand_digests),
        "recipe_step_distinct_digests_over_reencodings": len(step_digests),
        "note": "true-JCS digest is invariant across key-permutation and whitespace re-encodings, "
                "confirming structural (non-numeric) ambiguity is already prevented by "
                "canonicalization -- the residual ambiguity is purely numeric-type (G4).",
    }

    all_pass = all(g["passed"] for g in gates.values())
    diag = {
        "schema": "amphora.cro-protocol-packager.canonicalization-conformance-diagnostic.v1",
        "study_id": "canonicalization-conformance-v1",
        "module": "amphora-cro-protocol-packager",
        "run_type": "INDEPENDENT_CANONICALIZATION_CONFORMANCE_VS_SIGNED_FIXTURE",
        "authority": "AUDIT_ONLY",
        "headline": (
            "An independent, from-the-spec RFC 8785 JCS serializer (ECMA-262 number "
            "rendering, UTF-16 key ordering) shows the CRO candidate binding IS "
            "RFC-8785-conformant, but the formula binding is NOT: integer-valued float "
            "amounts (110.0) render as \"110.0\" under the module's json.dumps scheme vs "
            "\"110\" under true JCS, so the shipped formula_sha256 is a fixed Python-json "
            "digest, not the RFC-8785 digest the receipt labels it. This leaves a residual "
            "int-vs-float numeric-type ambiguity in the formula binding (same 110 g -> two "
            "digests) that adopting true RFC-8785 JCS would eliminate."),
        "purpose": (
            "Falsifiably test the *conformance* of the module's binding canonicalization to "
            "its cited standard (RFC 8785), rather than only its internal self-consistency, "
            "and quantify any residual ambiguity relative to the module's stated hypothesis "
            "that candidate+formula binding prevents ambiguous packets."),
        "non_circularity": (
            "The JCS serializer is authored from RFC 8785 / ECMA-262 7.1.12.1 and validated "
            "against an independent 16-vector number known-answer table; it never calls the "
            "Rust runtime nor the prior packet-binding harness, and consumes only fixture "
            "bytes. Divergence is demonstrated by two independent digest computations."),
        "theory_reference": [
            "IETF RFC 8785 (2020) JSON Canonicalization Scheme (JCS), Rundgren, Jordan, Erdtman",
            "ECMA-262 7.1.12.1 Number::toString (shortest round-tripping decimal)",
            "NIST FIPS 180-4 (2015) SHA-256",
        ],
        "fixture": {
            "path": "amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json",
            "fixture_sha256": sha(FX.read_bytes()),
            "fixture_id": p["fixture_id"],
        },
        "gates": gates,
        "all_gates_passed": all_pass,
        "closes": [
            "First conformance test of the module's binding canonicalization against its cited "
            "standard RFC 8785 (vs the prior receipt's self-consistency-only cross-check).",
            "Establishes the candidate binding is RFC-8785-conformant and precisely localizes "
            "the formula binding's non-conformance to integer-valued-float number rendering.",
            "Demonstrates and bounds a residual int/float numeric-type ambiguity in the formula "
            "binding, with an actionable fix (adopt true RFC-8785 JCS number serialization).",
        ],
        "does_not_close": [
            "Does not itself re-serialize the runtime's formula_sha256 under true JCS "
            "(Phase-1: change the Rust CanonicalHash to RFC-8785 number rendering + re-lock).",
            "Structural-content bindings remain intact; this is a numeric-encoding conformance "
            "finding, not a break of the packet-binding integrity established previously.",
            "No CRO acceptance, wet-lab, qualification, or release authority; no promotion, "
            "manifest edit, KPI/benchmark-lock edit, or scientific_readiness flip.",
        ],
        "promotes_authority": False, "flips_scientific_readiness": False,
        "modifies_manifest": False, "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False, "modifies_benchmark_lock": False,
        "human_review_performed": False,
    }
    return diag

if __name__ == "__main__":
    diag = run()
    out = json.dumps(diag, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out); print("WROTE", sys.argv[1])
    print("all_gates_passed", diag["all_gates_passed"])
    for k, v in diag["gates"].items():
        print(f"  {k}: {v['passed']}")
