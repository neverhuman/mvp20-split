#!/usr/bin/env python3
"""Deterministic builder for the amphora-optimizer-orchestrator
constraint-path-addressing corpus (path_addressing_corpus.v1.json).

The corpus is a locked set of (a) emitter-controlled `gates` fixture trees,
(b) declared constraint/display path texts, and (c) probe values used for
black-box identification of the node a path text actually resolves to.

Probe values are DERIVED, not hand-listed: they are exactly the set of
distinct node values occurring anywhere in any fixture (root objects
included), plus one sentinel value that occurs nowhere. Because every
scalar leaf in the fixture set is pairwise distinct, an equality probe that
accepts identifies the resolved node uniquely -- which is what makes the
identification black-box (it never reads the runtime resolver).

No randomness, no clock, no network. Output is canonical
(sort_keys=True, indent=2, trailing newline) so the SHA-256 is stable.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "path_addressing_corpus.v1.json"

# --- Fixtures: emitter-controlled `gates` trees ---------------------------
# Every scalar is globally unique so that equality-probe identification is
# injective. Fixture families are chosen to separate the three H0 claims:
#   F1  well-formed nested tree            -> injectivity
#   F2  keys the dot-grammar cannot spell  -> addressability
#   F3  flat dotted key + colliding nest   -> shadowing
#   F6  F3 minus the nest (baseline)       -> emitter-induced verdict flip
#   F4  arrays / non-object interiors / null / bool
#   F5  depth
FIXTURES = [
    {
        "fixture_id": "F1_nested_canonical",
        "note": "Well-formed nested gates tree; all keys dot-free and non-empty.",
        "gates": {
            "alpha": 1001,
            "beta": {"gamma": 1002, "delta": {"eps": 1003}},
        },
    },
    {
        "fixture_id": "F2_unspellable_keys",
        "note": "Gate keys that the dot-split grammar cannot spell: a key "
                "containing '.', the empty key, a key with a doubled dot, a "
                "trailing-dot key.",
        "gates": {
            "beta.gamma": 2001,
            "": 2002,
            "a..b": 2003,
            "trail.": 2004,
            "plain": 2005,
        },
    },
    {
        "fixture_id": "F3_shadow_collision",
        "note": "Flat dotted key 'beta.gamma' coexisting with nested "
                "beta->gamma. Tests which node the text 'beta.gamma' binds.",
        "gates": {
            "beta.gamma": 3001,
            "beta": {"gamma": 3002},
            "plain": 3003,
        },
    },
    {
        "fixture_id": "F4_arrays_and_types",
        "note": "Array interiors, array-of-object, JSON null, string, bool.",
        "gates": {
            "arr": [4001, 4002],
            "objarr": [{"k": 4003}],
            "nul": None,
            "str": "s4004",
            "flag": True,
            "plain": 4005,
        },
    },
    {
        "fixture_id": "F5_deep",
        "note": "Four-level nesting; depth control for the walk.",
        "gates": {
            "l1": {"l2": {"l3": {"l4": 5001}}},
            "plain": 5002,
        },
    },
    {
        "fixture_id": "F7_whitespace_key",
        "note": "A gate key that is a single ASCII space. The constraint site "
                "trims the declared path before its emptiness guard, so this "
                "key is unreachable there; the display site does not trim.",
        "gates": {
            " ": 7001,
            "plain": 7002,
        },
    },
    {
        "fixture_id": "F6_shadow_baseline",
        "note": "F3 with the nested object REMOVED. Differs from F3 only by "
                "keys an emitter may freely add; used for the verdict-flip "
                "experiment.",
        "gates": {
            "beta.gamma": 3001,
            "plain": 6001,
        },
    },
]

# --- Declared path texts --------------------------------------------------
# Applied to EVERY fixture (the cross product is deliberate: rows that are
# absent in a given fixture are informative negative controls).
PATHS = [
    ("P01", "alpha", "plain single segment"),
    ("P02", "beta", "interior object node"),
    ("P03", "beta.gamma", "canonical two-segment path"),
    ("P04", ".beta.gamma", "leading separator"),
    ("P05", "beta..gamma", "doubled interior separator"),
    ("P06", "beta.gamma.", "trailing separator"),
    ("P07", "...beta...gamma...", "separator padding on all sides"),
    ("P08", "beta.delta.eps", "three-segment path"),
    ("P09", "plain", "single segment present in most fixtures"),
    ("P10", "", "empty path text"),
    ("P11", " ", "whitespace-only path text"),
    ("P12", ".", "separator-only path text"),
    ("P13", "..", "double-separator-only path text"),
    ("P14", "a..b", "text equal to an F2 key containing a doubled dot"),
    ("P15", "trail.", "text equal to an F2 key with a trailing dot"),
    ("P16", "arr", "array-valued node"),
    ("P17", "arr.0", "array element by index"),
    ("P18", "arr.1", "second array element by index"),
    ("P19", "objarr.0.k", "member of an object inside an array"),
    ("P20", "objarr", "array-of-object node"),
    ("P21", "nul", "JSON null leaf"),
    ("P22", "str", "string leaf"),
    ("P23", "flag", "boolean leaf"),
    ("P24", "l1.l2.l3.l4", "four-segment deep path"),
    ("P25", "l1.l2", "interior node of the deep tree"),
    ("P26", "absent_key", "absent single segment"),
    ("P27", "beta.gamma.extra", "walk past a scalar leaf"),
    ("P28", "a.b", "text that dot-splits identically to the F2 key 'a..b'"),
]

SENTINEL = "__AMPHORA_NO_SUCH_GATE_VALUE__"


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def walk_nodes(value, prefix=()):
    """Yield (node_path, value) for the node itself and every descendant.

    node_path elements are str for object members and int for array indices.
    """
    yield (list(prefix), value)
    if isinstance(value, dict):
        for key in value:
            yield from walk_nodes(value[key], prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_nodes(item, prefix + (index,))


def main():
    node_index = []
    seen = {}
    for fixture in FIXTURES:
        for node_path, value in walk_nodes(fixture["gates"]):
            node_index.append({
                "fixture_id": fixture["fixture_id"],
                "node_path": node_path,
                "value_canonical": canon(value),
            })
            seen.setdefault(canon(value), value)

    probe_values = []
    for order, text in enumerate(sorted(seen)):
        probe_values.append({
            "probe_id": f"V{order:03d}",
            "value": seen[text],
            "value_canonical": text,
            "occurs_in_fixtures": sorted({
                row["fixture_id"] for row in node_index
                if row["value_canonical"] == text
            }),
        })
    probe_values.append({
        "probe_id": "VSENT",
        "value": SENTINEL,
        "value_canonical": canon(SENTINEL),
        "occurs_in_fixtures": [],
    })

    corpus = {
        "schema": "amphora.optimizer-orchestrator.path-addressing-corpus.v1",
        "corpus_id": "optimizer-constraint-path-addressing-v1",
        "generator": "build_path_corpus.py",
        "determinism": {
            "randomness": False, "clock": False, "network": False,
            "ordering": "fixtures in declaration order; paths in declaration "
                        "order; probe values sorted by canonical JSON text",
        },
        "identification_method": {
            "site_a": "black-box equality probing: a single hard constraint "
                      "at the declared path with operator '==' is swept over "
                      "every probe value; the unique probe value that yields "
                      "an authorization ACCEPT identifies the resolved node.",
            "site_b": "direct read-back: the display-KPI definition returns "
                      "the resolved value verbatim in RankedCandidate."
                      "display_kpis, so no probing is required.",
            "uniqueness_precondition": "all fixture scalars are pairwise "
                                       "distinct, so at most one probe value "
                                       "can match any resolved node",
        },
        "fixtures": FIXTURES,
        "paths": [
            {"path_id": pid, "text": text, "intent": intent}
            for pid, text, intent in PATHS
        ],
        "probe_values": probe_values,
        "node_index": node_index,
        "counts": {
            "fixtures": len(FIXTURES),
            "paths": len(PATHS),
            "probe_values": len(probe_values),
            "nodes_total": len(node_index),
            "site_a_cases": len(FIXTURES) * len(PATHS) * len(probe_values),
            "site_b_cases": len(FIXTURES) * len(PATHS),
        },
    }
    OUT.write_text(json.dumps(corpus, indent=2, sort_keys=True) + "\n")
    print("WROTE", OUT)
    print("fixtures", len(FIXTURES), "paths", len(PATHS),
          "probes", len(probe_values), "nodes", len(node_index))
    print("site_a_cases", corpus["counts"]["site_a_cases"])


if __name__ == "__main__":
    main()
