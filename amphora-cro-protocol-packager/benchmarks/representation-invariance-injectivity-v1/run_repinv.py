#!/usr/bin/env python3
"""Independent representation-invariance & injectivity audit for amphora-cro-protocol-packager.

Falsifiable hypothesis under test (a NEW axis, distinct from:
  * packet-binding-parity-v1  -> hash/render/signature SELF-CONSISTENCY + tamper DETECTION
  * canonicalization-conformance-v1 -> single-point BYTE-EQUALITY vs true RFC-8785 JCS
                                       (found formula binding diverges on one int/float token)):

  The CRO formula_sha256 binding is a well-defined INJECTIVE function of the *typed* canonical
  recipe, and its ONLY sensitivity to value-preserving re-encoding is JSON numeric TYPE
  (int vs float). Concretely we test, as a two-sided robustness characterization:

    (soundness / collision-resistance) distinct nominal recipes never share a digest;
    (invariance / fragility)          the value-preserving transform group leaves the digest
                                      invariant EXCEPT for numeric-type flips, whose orbit
                                      fragments the module digest into exactly 2^k classes
                                      (k = # integer-valued numeric leaves) while true
                                      RFC-8785 JCS collapses it to 1;
    (structural bound)                key-permutation + whitespace re-encodings are invariant
                                      under BOTH schemes (fragility is purely numeric-type);
    (semantic exactness)              a sub-tolerance amount perturbation still changes the
                                      digest under both schemes -> the binding is nominal-EXACT,
                                      not tolerance-aware.

AUDIT_ONLY. No runtime call, no promotion, no manifest/KPI/benchmark-lock/dataset edit.

Primary sources:
  - IETF RFC 8785 (2020) JSON Canonicalization Scheme (JCS), Rundgren/Jordan/Erdtman.
  - ECMA-262 7.1.12.1 Number::toString (shortest round-tripping decimal).
  - NIST FIPS 180-4 (2015) SHA-256.
  - Menezes/van Oorschot/Vanstone, Handbook of Applied Cryptography (1996), 9.2.2:
    a binding/commitment must be an injective (collision-free) map of its committed value.
"""
import base64, hashlib, json, copy
from decimal import Decimal
from pathlib import Path
from itertools import permutations, product

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FX = ROOT / "amphora-cro-protocol-packager/reference/mvp20/fixtures/known-answer-protocol-package.v1.json"

def sha(b): return hashlib.sha256(b).hexdigest()

# ---- module's ACTUAL binding scheme (parse -> compact sorted json.dumps -> sha256) ----
def py_scheme(o): return json.dumps(o, separators=(",", ":"), sort_keys=True).encode()

# ---- TRUE RFC 8785 JCS (from spec; number path = ECMA-262 7.1.12.1) --------------------
def ecma262_number(x):
    if isinstance(x, bool): raise TypeError("bool is not a number")
    if isinstance(x, int): return str(x)
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("non-finite number not permitted in JSON")
    if x == 0: return "0"
    sign = "-" if x < 0 else ""
    d = Decimal(repr(abs(x)))
    _, digits, exp = d.as_tuple()
    digits = list(digits)
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop(); exp += 1
    s = "".join(map(str, digits)); k = len(s); n = exp + k
    if k <= n <= 21: return sign + s + "0" * (n - k)
    if 0 < n <= 21: return sign + s[:n] + "." + s[n:]
    if -6 < n <= 0: return sign + "0." + "0" * (-n) + s
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

# ---- numeric-leaf discovery + type-flip orbit -----------------------------------------
def numeric_leaf_paths(o, prefix=()):
    """Yield paths to numeric leaves (excluding bool) that are integer-VALUED (flippable
    between JSON int and float without changing the mathematical value)."""
    if isinstance(o, bool):
        return
    if isinstance(o, (int, float)):
        v = float(o)
        if v == v and v not in (float("inf"), float("-inf")) and v.is_integer():
            yield prefix
        return
    if isinstance(o, dict):
        for k, v in o.items():
            yield from numeric_leaf_paths(v, prefix + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from numeric_leaf_paths(v, prefix + (i,))

def set_at(o, path, val):
    cur = o
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = val

def apply_type_mask(base, paths, mask):
    """mask[i]=True -> encode leaf i as int; False -> as float."""
    o = copy.deepcopy(base)
    for use_int, path in zip(mask, paths):
        cur = o
        for p in path[:-1]:
            cur = cur[p]
        v = cur[path[-1]]
        cur[path[-1]] = int(v) if use_int else float(v)
    return o

def run():
    fx = json.loads(FX.read_bytes())
    p = fx["payload"]
    steps = p["recipe_steps"]
    gates = {}

    # anchor: module-scheme identity digest reproduces the shipped formula_sha256
    id_module = sha(py_scheme(steps))
    id_jcs = sha(jcs_bytes(steps))
    anchor_ok = (id_module == p["formula_sha256"])

    # G1: injectivity / collision-resistance on a DESIGNED distinct-recipe lattice --------
    def base_steps():
        return copy.deepcopy(steps)
    variants = {}
    variants["as_shipped"] = base_steps()
    v = base_steps(); v[0]["amount"] = 111.0;          variants["amount0_110_to_111"] = v
    v = base_steps(); v[1]["amount"] = 41.0;           variants["amount1_40_to_41"]  = v
    v = base_steps(); v[0]["ingredient_id"] = "synthetic-resin-b"; variants["ingredient0_swap"] = v
    v = base_steps(); v[0]["sequence"], v[1]["sequence"] = 2, 1;   variants["sequence_swap"] = v
    v = base_steps(); v[0]["tolerance"] = {"minus": 0.4, "plus": 0.6}; variants["tolerance0_change"] = v
    v = base_steps(); v[0]["action"] = "MIX";          variants["action0_add_to_mix"] = v
    v = base_steps(); v[0]["unit"] = "kg";             variants["unit0_g_to_kg"] = v
    v = base_steps(); v.append({"action": "ADD", "amount": 5.0, "ingredient_id": "accelerator",
                                "sequence": 3, "tolerance": {"minus": 0.1, "plus": 0.1}, "unit": "g"})
    variants["append_third_step"] = v
    v = base_steps(); del v[0]["tolerance"];           variants["drop_tolerance0"] = v
    v = base_steps(); v[0]["amount"] = 110.5;          variants["amount0_110_to_110p5"] = v
    v = base_steps(); v = [v[1], v[0]];                variants["list_reorder"] = v
    mod_map = {name: sha(py_scheme(o)) for name, o in variants.items()}
    jcs_map = {name: sha(jcs_bytes(o)) for name, o in variants.items()}
    n_var = len(variants)
    mod_collisions = n_var - len(set(mod_map.values()))
    jcs_collisions = n_var - len(set(jcs_map.values()))
    gates["G1_injectivity_no_collision"] = {
        "passed": (mod_collisions == 0) and (jcs_collisions == 0),
        "n_distinct_nominal_recipes": n_var,
        "module_scheme_distinct_digests": len(set(mod_map.values())),
        "true_jcs_distinct_digests": len(set(jcs_map.values())),
        "module_scheme_collisions": mod_collisions,
        "true_jcs_collisions": jcs_collisions,
        "variant_ids": sorted(variants.keys()),
        "source": "HAC 1996 9.2.2 binding must be an injective map of the committed value",
        "note": "On a designed lattice of nominally distinct recipes (amount, ingredient, "
                "sequence, tolerance, action, unit, step-count, list-order), both the module "
                "scheme and true JCS assign a unique digest to each -> the binding never "
                "UNDER-binds (no false-same collision). Complements the random tamper probes "
                "of packet-binding-parity-v1 with a structured injectivity lattice.",
    }

    # G2: value-preserving numeric-TYPE orbit -> module fragments into 2^k, JCS collapses to 1
    paths = list(numeric_leaf_paths(steps))
    k = len(paths)
    mod_orbit, jcs_orbit = set(), set()
    for mask in product([True, False], repeat=k):
        o = apply_type_mask(steps, paths, mask)
        mod_orbit.add(sha(py_scheme(o)))
        jcs_orbit.add(sha(jcs_bytes(o)))
    gates["G2_type_orbit_module_fragments_jcs_collapses"] = {
        "passed": (len(mod_orbit) == 2 ** k) and (len(jcs_orbit) == 1) and (k >= 1),
        "integer_valued_numeric_leaves_k": k,
        "flippable_leaf_paths": [list(pp) for pp in paths],
        "predicted_module_classes_2_pow_k": 2 ** k,
        "observed_module_scheme_classes": len(mod_orbit),
        "observed_true_jcs_classes": len(jcs_orbit),
        "note": "Every integer-valued numeric leaf (2 amounts + 2 sequence indices = k=4) may be "
                "legally spelled as JSON int or float by a conformant producer. Under the module "
                "scheme each independent spelling flips one digest bit, fragmenting the SAME "
                "nominal recipe into 2^k = 16 distinct formula_sha256 values. True RFC-8785 JCS "
                "normalizes all of them to 1. This is the quantified size of the ambiguity "
                "surface, extending canonicalization-conformance-v1's single-token int/float "
                "example (which flipped only `amount`) to the full numeric-leaf set.",
    }

    # G3: structural re-encodings are invariant under BOTH schemes (fragility is purely type)
    def structural_reencodings(obj, n=6):
        outs = []
        if isinstance(obj, dict):
            keys = list(obj.keys())
            for perm in list(permutations(keys))[:n]:
                d = {kk: obj[kk] for kk in perm}
                for indent in (None, 2, 4):
                    outs.append(json.loads(json.dumps(d, indent=indent)))
        else:
            for indent in (None, 1, 2, 4):
                outs.append(json.loads(json.dumps(obj, indent=indent)))
        return outs
    probe = steps[0]
    mod_struct = {sha(py_scheme(v)) for v in structural_reencodings(probe)}
    jcs_struct = {sha(jcs_bytes(v)) for v in structural_reencodings(probe)}
    gates["G3_structural_invariance_both_schemes"] = {
        "passed": (len(mod_struct) == 1) and (len(jcs_struct) == 1),
        "module_scheme_structural_classes": len(mod_struct),
        "true_jcs_structural_classes": len(jcs_struct),
        "note": "Key-permutation and whitespace/indentation re-encodings leave BOTH the module "
                "scheme (sort_keys+separators) and true JCS digests invariant -> the residual "
                "fragility is bounded to numeric-TYPE alone; structural ambiguity is already "
                "prevented in the live scheme.",
    }

    # G4: semantic exactness -- a SUB-TOLERANCE amount perturbation still changes the digest
    tol = steps[0]["tolerance"]["plus"]                      # +0.5 g on 110 g
    perturbed = copy.deepcopy(steps)
    delta = tol / 2.0                                         # 0.25 g, strictly within +/-0.5
    perturbed[0]["amount"] = float(steps[0]["amount"]) + delta
    mod_pert = sha(py_scheme(perturbed)); jcs_pert = sha(jcs_bytes(perturbed))
    gates["G4_binding_is_nominal_exact_not_tolerance_aware"] = {
        "passed": (mod_pert != id_module) and (jcs_pert != id_jcs),
        "declared_plus_tolerance_g": tol,
        "applied_perturbation_g": delta,
        "perturbation_within_tolerance": delta < tol,
        "module_scheme_digest_changed": mod_pert != id_module,
        "true_jcs_digest_changed": jcs_pert != id_jcs,
        "note": "Changing amount 110.0 -> 110.25 g (inside the declared +/-0.5 g tolerance band) "
                "changes the digest under both schemes. The binding therefore commits the NOMINAL "
                "recipe point, not the tolerance-admissible set -- an intended-but-previously-"
                "unstated exactness property. A CRO measuring an in-spec 110.25 g must still "
                "reference the nominal packet; the digest is not a spec-band membership test.",
    }

    # G5: adopting RFC-8785 JCS would unify the module's 2^k type classes to 1
    gates["G5_jcs_relock_unifies_orbit"] = {
        "passed": (len(jcs_orbit) == 1) and (len(mod_orbit) > 1),
        "module_classes_before": len(mod_orbit),
        "jcs_classes_after": len(jcs_orbit),
        "reduction_factor": len(mod_orbit) // max(1, len(jcs_orbit)),
        "note": "Re-locking the Rust CanonicalHash to RFC-8785 JCS number rendering collapses the "
                "16-way numeric-type ambiguity to a single canonical digest -- the concrete "
                "Phase-1 fix, consistent with canonicalization-conformance-v1's recommendation.",
    }

    all_pass = all(g["passed"] for g in gates.values()) and anchor_ok
    diag = {
        "schema": "amphora.cro-protocol-packager.representation-invariance-diagnostic.v1",
        "study_id": "representation-invariance-injectivity-v1",
        "module": "amphora-cro-protocol-packager",
        "run_type": "INDEPENDENT_REPRESENTATION_INVARIANCE_AND_INJECTIVITY_VS_SIGNED_FIXTURE",
        "authority": "AUDIT_ONLY",
        "headline": (
            "An independent from-spec RFC-8785 JCS serializer characterizes the CRO formula "
            "binding as a two-sided robustness object: (i) it is INJECTIVE -- 12 nominally "
            "distinct recipes yield 12 distinct digests under both the module scheme and true "
            "JCS, so it never under-binds (no false-same collision); (ii) its ONLY value-"
            "preserving fragility is JSON numeric TYPE -- the k=4 integer-valued numeric leaves "
            "(2 amounts + 2 sequence indices) fragment the SAME nominal recipe into 2^4=16 "
            "distinct module digests, which true RFC-8785 JCS collapses to 1; (iii) key-order "
            "and whitespace re-encodings are invariant under both schemes; and (iv) an in-spec "
            "sub-tolerance perturbation still changes the digest, so the binding commits the "
            "nominal recipe point, not the tolerance band. The fragility is one-directional: "
            "the binding OVER-binds (fragile to benign re-encoding) but never UNDER-binds."),
        "purpose": (
            "Quantify the invariance group and injectivity of the CRO formula binding -- "
            "properties neither packet-binding-parity-v1 (self-consistency + tamper detection) "
            "nor canonicalization-conformance-v1 (single-point byte-equality vs JCS) measured -- "
            "and size the numeric-type ambiguity surface (2^k) that an RFC-8785 re-lock removes."),
        "non_circularity": (
            "The oracle never invokes the Rust CroProtocolPackageV2 runtime; it re-derives every "
            "digest from the checked-in fixture bytes using CPython stdlib json/hashlib and a "
            "from-spec RFC-8785 JCS serializer. The module scheme is reproduced independently as "
            "compact sorted json.dumps and anchored to the shipped formula_sha256."),
        "theory_reference": [
            "IETF RFC 8785 (2020) JSON Canonicalization Scheme",
            "ECMA-262 7.1.12.1 Number::toString",
            "NIST FIPS 180-4 (2015) SHA-256",
            "Menezes/van Oorschot/Vanstone, Handbook of Applied Cryptography (1996), 9.2.2",
        ],
        "fixture": {"path": str(FX.relative_to(ROOT)), "fixture_id": p.get("fixture_id"),
                    "sha256": sha(FX.read_bytes()),
                    "shipped_formula_sha256": p["formula_sha256"],
                    "module_scheme_identity_digest": id_module,
                    "module_scheme_anchor_matches_shipped": anchor_ok},
        "gates": gates,
        "all_gates_passed": all_pass,
        "closes": [
            "Injectivity (collision-resistance) of the formula binding on a designed distinct-"
            "recipe lattice: no false-same under module scheme or true JCS.",
            "Quantified size of the value-preserving numeric-type ambiguity surface: 2^k=16 module "
            "digest classes for one nominal recipe, vs 1 under RFC-8785 JCS.",
            "Bound on the fragility: structural (key-order/whitespace) re-encodings are invariant; "
            "only numeric TYPE is at issue.",
            "Semantic characterization: the binding is nominal-exact, not tolerance-aware.",
        ],
        "does_not_close": [
            "Reason-level parity vs the Rust runtime error taxonomy (Phase-1 differential harness).",
            "Any CRO acceptance, wet-lab execution, or product qualification (Phase-1 external).",
            "The RFC-8785 JCS re-lock itself, which requires editing + re-locking the Rust "
            "CanonicalHash and the signed benchmark -- human dual-identity Phase-0 ceremony, "
            "out of scope for this AUDIT_ONLY cron.",
        ],
    }
    return diag

if __name__ == "__main__":
    import sys
    diag = run()
    out = json.dumps(diag, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(out)
        print("WROTE", sys.argv[1], "all_gates_passed", diag["all_gates_passed"])
    else:
        print(out)
