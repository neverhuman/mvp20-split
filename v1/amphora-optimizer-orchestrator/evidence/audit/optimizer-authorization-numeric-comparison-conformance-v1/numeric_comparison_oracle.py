#!/usr/bin/env python3
"""Independent SPEC-SIDE semantics for the amphora-optimizer-orchestrator
hard-constraint comparison surface.

This module does NOT import, link, or read the Rust runtime. It implements two
comparison semantics directly from published standards, plus one explicitly
POST-HOC descriptive model of the observed runtime:

  S1 -- RFC 8259 / ECMA-404 mathematical-value semantics.
        IETF STD 90 / RFC 8259 (Bray, ed., Dec 2017, DOI 10.17487/RFC8259) Sec.6:
        a JSON number literal denotes a mathematical number; the grammar admits
        [-] int [frac] [exp] and admits NO NaN / Infinity tokens. ECMA-404 2nd
        ed. (Dec 2017) Sec.8 is identical. Under S1 two literals denoting the
        same mathematical value ARE the same number: 110 == 110.0 == 1.10e2.
        Implemented with exact rationals (fractions.Fraction) -- no float ever
        touches S1.

  S2 -- IEEE 754-2019 binary64 semantics.
        IEEE Std 754-2019 (DOI 10.1109/IEEESTD.2019.8766229) Sec.5.11
        compareQuietEqual / compareQuietGreater / compareQuietGreaterEqual /
        compareQuietLess / compareQuietLessEqual, over the correctly-rounded
        (Sec.4.3.1 roundTiesToEven) binary64 image of each literal.
        Under S2 -0.0 == +0.0 and 2^53+1 rounds onto 2^53.

  M3 -- POST-HOC descriptive model of serde_json 1.0.150 Value semantics.
        NOT a pre-registered prediction: it is a characterization fitted after
        observing the live runtime, retained only because a model that explains
        100% of observed verdicts is the reusable artifact. Flagged as post-hoc
        everywhere it is reported.

Reachability policy (pre-registered): a literal is admissible through the
front door iff it is a valid RFC 8259 value AND, if numeric, its correctly
rounded binary64 image is finite -- the binary64 interoperability limit of
RFC 7493 (I-JSON, Bray ed., Mar 2015, DOI 10.17487/RFC7493) Sec.2.2.

Interoperability boundary (pre-registered): RFC 7493 Sec.2.2 declares integers
outside [-(2^53 - 1), 2^53 - 1] non-interoperable; S1/S2 ordering divergence is
predicted to be confined to that region.
"""

import re
from fractions import Fraction

# RFC 8259 Sec.6 number grammar, anchored.
_NUM_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$")
# RFC 8259 Sec.7 string grammar, restricted to the plain literals in the corpus.
_STR_RE = re.compile(r'^"[^"\\\x00-\x1f]*"$')

TWO_53 = 2 ** 53
IJSON_MAX = TWO_53 - 1  # RFC 7493 Sec.2.2 interoperable integer magnitude.

NEG_ZERO = "NEG_ZERO"  # sentinel: exact value 0 carrying a minus sign


class SpecValue:
    """Tagged RFC 8259 value. `kind` in {number,string,bool,null,array,object}."""

    __slots__ = ("kind", "exact", "neg_zero", "literal", "raw")

    def __init__(self, kind, literal, exact=None, neg_zero=False, raw=None):
        self.kind = kind
        self.literal = literal
        self.exact = exact          # Fraction for numbers, else None
        self.neg_zero = neg_zero    # RFC 8259 permits a leading '-' on zero
        self.raw = raw              # python value for non-numeric scalars


def parse_rfc8259_scalar(text):
    """Strict RFC 8259 / ECMA-404 scalar parse. Returns SpecValue or None.

    None means the token is not a valid JSON value at all (e.g. NaN, Infinity):
    such a document cannot be produced by a conforming serializer nor accepted
    by a conforming parser."""
    if _NUM_RE.match(text):
        neg = text.startswith("-")
        body = text[1:] if neg else text
        if "e" in body or "E" in body:
            mant, _, exp = re.split(r"([eE])", body, maxsplit=1)[0], None, body.split("e")[-1].split("E")[-1]
            mant = re.split(r"[eE]", body)[0]
            exp = int(re.split(r"[eE]", body)[1])
        else:
            mant, exp = body, 0
        if "." in mant:
            ip, fp = mant.split(".")
        else:
            ip, fp = mant, ""
        digits = ip + fp
        value = Fraction(int(digits), 10 ** len(fp)) * Fraction(10) ** exp
        if neg:
            value = -value
        return SpecValue("number", text, exact=value, neg_zero=(neg and value == 0))
    if text == "true":
        return SpecValue("bool", text, raw=True)
    if text == "false":
        return SpecValue("bool", text, raw=False)
    if text == "null":
        return SpecValue("null", text, raw=None)
    if _STR_RE.match(text):
        return SpecValue("string", text, raw=text[1:-1])
    if text == "[]":
        return SpecValue("array", text, raw=[])
    if text == "{}":
        return SpecValue("object", text, raw={})
    return None


def to_binary64(exact, neg_zero=False):
    """IEEE 754-2019 Sec.4.3.1 roundTiesToEven image of an exact rational.

    Returns (float, finite: bool). Non-finite means the literal exceeds the
    binary64 range and is therefore outside the RFC 7493 Sec.2.2 limit."""
    if exact == 0:
        return (-0.0 if neg_zero else 0.0), True
    try:
        f = float(exact)  # Fraction.__float__ is correctly rounded
    except OverflowError:
        f = float("inf") if exact > 0 else float("-inf")
    if f != f or f in (float("inf"), float("-inf")):
        return f, False
    return f, True


def reachable(text):
    """Pre-registered front-door reachability predicate (RFC 8259 + RFC 7493)."""
    sv = parse_rfc8259_scalar(text)
    if sv is None:
        return False, "NOT_A_JSON_VALUE"
    if sv.kind != "number":
        return True, "NON_NUMERIC_JSON_VALUE"
    _, finite = to_binary64(sv.exact, sv.neg_zero)
    return (True, "NUMBER_IN_BINARY64_RANGE") if finite else (False, "NUMBER_OUT_OF_BINARY64_RANGE")


# ---------------------------------------------------------------- S1 (exact)

def _json_structural_eq(a, b):
    """Type-sensitive equality for non-numeric JSON values (RFC 8259 Sec.3-5).
    A string is never equal to a number; true is never equal to 1."""
    if a.kind != b.kind:
        return False
    if a.kind in ("string", "bool"):
        return a.raw == b.raw
    if a.kind == "null":
        return True
    if a.kind in ("array", "object"):
        return a.raw == b.raw
    raise AssertionError("numbers handled elsewhere")


def s1_compare(a, b, op):
    """RFC 8259 mathematical-value semantics. Ordering on non-numbers is
    undefined and therefore fails closed (False)."""
    both_num = a.kind == "number" and b.kind == "number"
    if op == "==":
        return (a.exact == b.exact) if both_num else _json_structural_eq(a, b)
    if op == "!=":
        return not s1_compare(a, b, "==")
    if not both_num:
        return False
    x, y = a.exact, b.exact
    return {">=": x >= y, "<=": x <= y, ">": x > y, "<": x < y}[op]


# ------------------------------------------------------------- S2 (binary64)

def s2_compare(a, b, op):
    """IEEE 754-2019 Sec.5.11 compareQuiet* over the binary64 images.
    Non-numeric operands: equality falls back to RFC 8259 structural equality
    (IEEE 754 does not define them); ordering fails closed."""
    both_num = a.kind == "number" and b.kind == "number"
    if not both_num:
        if op == "==":
            return _json_structural_eq(a, b)
        if op == "!=":
            return not _json_structural_eq(a, b)
        return False
    x, _ = to_binary64(a.exact, a.neg_zero)
    y, _ = to_binary64(b.exact, b.neg_zero)
    if op == "==":
        return x == y                      # compareQuietEqual: -0 == +0
    if op == "!=":
        return x != y                      # compareQuietNotEqual
    return {">=": x >= y, "<=": x <= y, ">": x > y, "<": x < y}[op]


# ------------------------------------------- M3 (POST-HOC descriptive model)

I64_MIN, I64_MAX = -(2 ** 63), 2 ** 63 - 1
U64_MAX = 2 ** 64 - 1


def m3_tag(sv):
    """POST-HOC: which serde_json::value::Number variant a literal lands in."""
    t = sv.literal
    if re.search(r"[.eE]", t):
        return "F64"
    n = int(t)
    if t.startswith("-"):
        if n == 0:
            return "F64"        # observed: serde_json parses "-0" as f64 -0.0
        return "I64" if n >= I64_MIN else "F64"
    return "U64" if n <= U64_MAX else "F64"


def m3_compare(a, b, op):
    """POST-HOC descriptive model of serde_json Value comparison as used by
    amphora_core::comparison_passes: `==`/`!=` use variant-tagged Value
    equality; the four ordering operators use as_f64 (binary64)."""
    both_num = a.kind == "number" and b.kind == "number"
    if op in ("==", "!="):
        if both_num:
            ta, tb = m3_tag(a), m3_tag(b)
            if ta != tb:
                eq = False
            elif ta == "F64":
                xa, _ = to_binary64(a.exact, a.neg_zero)
                xb, _ = to_binary64(b.exact, b.neg_zero)
                eq = xa == xb
            else:
                eq = int(a.literal) == int(b.literal)
        else:
            eq = _json_structural_eq(a, b)
        return eq if op == "==" else (not eq)
    if not both_num:
        return False
    return s2_compare(a, b, op)
