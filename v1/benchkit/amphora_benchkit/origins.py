"""Verbatim extraction of ORIGINAL in-tree implementations for bit-identity
testing.

`load_origin` never hand-copies code: it parses the original benchmark file,
keeps only the requested top-level FunctionDef / ClassDef / Assign nodes (plus
all import statements, each individually guarded), compiles exactly those AST
nodes and executes them in a fresh namespace.  The "original" side of every
determinism test is therefore the tree's own bytes, provenanced by the file's
sha256 (available as ns["__origin_sha256__"]).

Top-level script *statements* (the parts that run the benchmark and write
receipts) are never executed unless their assignment target is explicitly
requested by name, so signed artifacts cannot be touched by loading an origin.
"""
import ast
import hashlib
from pathlib import Path


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _assign_names(node):
    out = []
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                out.append(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                for e in t.elts:
                    if isinstance(e, ast.Name):
                        out.append(e.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        out.append(node.target.id)
    return out


def load_origin(path, names, extra=None):
    """Execute only the named top-level defs/assigns of `path`; return the
    namespace. Imports in the file are executed (individually, ImportError
    tolerated) so the extracted functions see their real dependencies.
    Execution order is the file's own statement order."""
    path = str(path)
    raw = Path(path).read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    names = set(names)
    ns = {"__name__": "origin::" + path, "__file__": path}
    if extra:
        ns.update(extra)
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            try:
                exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), ns)
            except ImportError:
                pass
            continue
        take = False
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            take = node.name in names
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            take = any(n in names for n in _assign_names(node))
        if take:
            exec(compile(ast.Module(body=[node], type_ignores=[]), path, "exec"), ns)
    ns["__origin_sha256__"] = hashlib.sha256(raw).hexdigest()
    return ns
