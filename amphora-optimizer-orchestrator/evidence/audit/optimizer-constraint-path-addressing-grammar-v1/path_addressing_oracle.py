#!/usr/bin/env python3
"""Independent (non-runtime) oracle for the amphora-optimizer-orchestrator
constraint/display PATH-ADDRESSING grammar.

This module does NOT import, link, or invoke the Rust runtime. It models two
addressing grammars from their published/declared semantics and derives the
soundness properties that the live differential then measures:

  G_shipped -- the dotted grammar declared by the optimizer request contract
    (`section` + `path`, path segments separated by '.'): the path text is
    split on '.', empty segments are discarded, and the remaining segments
    are applied left-to-right as JSON *object member* lookups. This is an
    ad-hoc addressing scheme with no normative specification.

  G_pointer -- RFC 6901 JSON Pointer, the IETF standard addressing syntax
    for JSON documents.

Published anchors
-----------------
  * RFC 6901, "JavaScript Object Notation (JSON) Pointer", P. Bryan (ed.),
    K. Zyp, M. Nottingham, IETF, April 2013, DOI 10.17487/RFC6901.
    - Sec. 3: a pointer is a (possibly empty) sequence of '/'-prefixed
      reference tokens; the empty pointer denotes the whole document.
    - Sec. 3: escaping -- '~1' denotes '/', '~0' denotes '~'. Every other
      character, INCLUDING '.', is literal. Hence every object member name
      is spellable, including the empty name and names containing dots.
    - Sec. 4: array elements are addressed by decimal index tokens.
  * RFC 8259, "The JavaScript Object Notation (JSON) Data Interchange
    Format", T. Bray (ed.), IETF, December 2017, DOI 10.17487/RFC8259.
    - Sec. 4: an object member name is any JSON string; the empty string and
      strings containing '.' are legal member names. Objects are unordered.
  * J. H. Saltzer and M. D. Schroeder, "The Protection of Information in
    Computer Systems", Proc. IEEE 63(9):1278-1308, 1975 -- complete
    mediation: every access to every object must be checked.
  * J. P. Anderson, "Computer Security Technology Planning Study",
    ESD-TR-73-51, 1972 -- reference monitor.
  * N. Hardy, "The Confused Deputy (or why capabilities might have been
    invented)", ACM SIGOPS Operating Systems Review 22(4):36-38, 1988 --
    a privileged component acting on a name resolved in the wrong context.
  * MITRE CWE-41 "Improper Resolution of Path Equivalence" and CWE-706 "Use
    of Incorrectly-Resolved Name or Reference" -- the two defect classes a
    non-injective / shadowing name resolver exhibits.

Falsifiable hypothesis under test (H0): the shipped dotted grammar is a
SOUND and COMPLETE addressing function over the emitter-controlled `gates`
tree, i.e.

  H0a INJECTIVITY   -- distinct accepted path texts address distinct nodes.
  H0b ADDRESSABILITY-- every node of a legal RFC 8259 gates tree is
                       addressable by some path text.
  H0c NON-SHADOWING -- the node a path text binds does not depend on keys
                       that the envelope emitter may independently add.
"""

# --- runtime reason strings (declared contract surface, re-declared here) --
REASON_DECL = "optimizer constraint declaration is unknown, duplicate, or malformed"
REASON_PATH = "optimizer constraint path is absent or unknown"
REASON_FAIL = "optimizer hard constraint failed"

MALFORMED = "MALFORMED_DECLARATION"
ABSENT = "PATH_ABSENT"
RESOLVED = "RESOLVED"


# ---------------------------------------------------------------------------
# G_shipped
# ---------------------------------------------------------------------------
def segments(path_text):
    """Dot-split with empty segments discarded (the shipped grammar)."""
    return [part for part in path_text.split(".") if part != ""]


def member_get(value, key):
    """Model of serde_json `Value::get(&str)`.

    A string index selects an object member. Indexing an array, or any
    scalar, with a string yields nothing -- serde_json's `Index` impl for
    `&str` returns None for every non-object value.
    """
    if isinstance(value, dict) and key in value:
        return True, value[key]
    return False, None


def resolve_constraint_shipped(gates, path_text):
    """Model of the constraint-site resolver in authorize_optimizer_request.

    Returns (status, value, reason). The declaration guard rejects a path
    whose text is empty after trimming ASCII/Unicode whitespace; a path that
    survives the guard but yields no segments is reported as absent, because
    the resolver requires at least one segment before it may consult `gates`.
    """
    if path_text.strip() == "":
        return MALFORMED, None, REASON_DECL
    parts = segments(path_text)
    if not parts:
        return ABSENT, None, REASON_PATH
    found, current = member_get(gates, parts[0])
    if not found:
        return ABSENT, None, REASON_PATH
    for part in parts[1:]:
        found, current = member_get(current, part)
        if not found:
            return ABSENT, None, REASON_PATH
    return RESOLVED, current, None


def resolve_display_shipped(section_value, path_text):
    """Model of `envelope_value`, the display-site resolver.

    Same dot-split, but folded from the section value with no declaration
    guard and no minimum-segment requirement: a path that yields no segments
    resolves to the SECTION ITSELF.
    """
    parts = segments(path_text)
    current = section_value
    for part in parts:
        found, current = member_get(current, part)
        if not found:
            return ABSENT, None
    return RESOLVED, current


def constraint_verdict_shipped(gates, path_text, expected_canonical, canon):
    """Predicted authorization verdict for a single '==' hard constraint."""
    status, value, reason = resolve_constraint_shipped(gates, path_text)
    if status != RESOLVED:
        return "REJECT", reason
    if canon(value) == expected_canonical:
        return "ACCEPT", None
    return "REJECT", REASON_FAIL


# ---------------------------------------------------------------------------
# G_pointer -- RFC 6901
# ---------------------------------------------------------------------------
def pointer_escape(token):
    """RFC 6901 Sec. 3: '~' -> '~0', '/' -> '~1' (in that order)."""
    return token.replace("~", "~0").replace("/", "~1")


def pointer_unescape(token):
    """RFC 6901 Sec. 4: '~1' -> '/' first, then '~0' -> '~'."""
    return token.replace("~1", "/").replace("~0", "~")


def pointer_for(node_path):
    """Canonical RFC 6901 pointer for a node path of member names / indices."""
    out = ""
    for step in node_path:
        out += "/" + (str(step) if isinstance(step, int)
                      else pointer_escape(step))
    return out


def resolve_pointer(document, pointer):
    """RFC 6901 evaluation. Returns (status, value)."""
    if pointer == "":
        return RESOLVED, document
    if not pointer.startswith("/"):
        return ABSENT, None
    current = document
    for raw in pointer.split("/")[1:]:
        token = pointer_unescape(raw)
        if isinstance(current, dict):
            if token not in current:
                return ABSENT, None
            current = current[token]
        elif isinstance(current, list):
            # RFC 6901 Sec. 4: decimal index, no leading zeros beyond "0".
            if not token.isdigit() or (len(token) > 1 and token[0] == "0"):
                return ABSENT, None
            index = int(token)
            if index >= len(current):
                return ABSENT, None
            current = current[index]
        else:
            return ABSENT, None
    return RESOLVED, current


# ---------------------------------------------------------------------------
# Derived soundness properties
# ---------------------------------------------------------------------------
def addressable_under_shipped(node_path):
    """Characterisation theorem for G_shipped at the constraint site.

    A node is reachable by SOME dotted path text iff

      (i)   its root path is non-empty -- the resolver requires at least one
            segment before it may consult `gates`, so the gates root itself
            is unreachable;
      (ii)  every step is an object member name, not an array index -- the
            walk uses string member lookup only;
      (iii) every step is non-empty and contains no '.' -- dot-splitting with
            empty segments discarded can never produce such a segment; and
      (iv)  the joined text survives the declaration guard, which trims the
            path text and rejects it if nothing remains. The join contains a
            '.' whenever there are two or more steps, so (iv) bites only on
            the single-step case where that one member name is entirely
            whitespace.

    (=>) is (ii)+(iii)+(i)+(iv) read off the resolver and its guard.
    (<=) If (i)-(iv) hold, the '.'-join of the steps dot-splits back to
    exactly those steps and each lookup finds its member.
    """
    if len(node_path) == 0:
        return False
    for step in node_path:
        if isinstance(step, int):
            return False
        if step == "" or "." in step:
            return False
    return ".".join(node_path).strip() != ""


def canonical_text_for_shipped(node_path):
    """The dotted text that reaches an addressable node (None otherwise)."""
    if not addressable_under_shipped(node_path):
        return None
    return ".".join(node_path)


def addressable_under_pointer(node_path):
    """RFC 6901 addresses every node of every RFC 8259 document.

    Object member names are escaped (Sec. 3), array elements are addressed
    by index (Sec. 4), and the empty pointer denotes the root, so the
    addressing function is total.
    """
    return True
