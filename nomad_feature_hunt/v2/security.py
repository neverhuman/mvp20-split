from __future__ import annotations

import ast
import re
from pathlib import Path

from .constants import PLUGIN_LIMIT_BYTES


ALLOWED_IMPORTS = {"collections", "functools", "itertools", "math", "numpy", "scipy", "statistics"}
FORBIDDEN_CALLS = {
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
    "__import__",
}
FORBIDDEN_NAMES = {
    "builtins",
    "ftplib",
    "httpx",
    "os",
    "pathlib",
    "requests",
    "secrets",
    "socket",
    "subprocess",
    "sys",
    "urllib",
}
FORBIDDEN_TEXT = re.compile(
    r"(?:formation_energy_ev_natom|bandgap_energy_ev|test[_ -]?labels?|train[_ -]?labels?|targets?\.npy)",
    re.IGNORECASE,
)


def static_check_plugin(source: str) -> list[str]:
    errors: list[str] = []
    size = len(source.encode("utf-8"))
    if size > PLUGIN_LIMIT_BYTES:
        errors.append(f"plugin is {size} bytes; limit is {PLUGIN_LIMIT_BYTES}")
    if FORBIDDEN_TEXT.search(source):
        errors.append("plugin references a forbidden target or label path")
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return errors + [f"syntax error: {error.msg} at line {error.lineno}"]
    definitions: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root not in ALLOWED_IMPORTS:
                    errors.append(f"import is not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root not in ALLOWED_IMPORTS:
                errors.append(f"import is not allowed: {node.module or ''}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                errors.append(f"call is not allowed: {node.func.id}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            errors.append(f"name is not allowed: {node.id}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            errors.append(f"{type(node).__name__.lower()} declarations are not allowed")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "compute_family":
            definitions.append(node)
    if len(definitions) != 1:
        errors.append("plugin must define exactly one compute_family function")
    else:
        function = definitions[0]
        positional = [*function.args.posonlyargs, *function.args.args]
        if [argument.arg for argument in positional] != ["structure", "config"]:
            errors.append("compute_family signature must be (structure, config)")
        if function.args.vararg or function.args.kwarg or function.args.kwonlyargs:
            errors.append("compute_family may not accept variadic or keyword-only arguments")
        if isinstance(function, ast.AsyncFunctionDef):
            errors.append("compute_family may not be async")
    return sorted(set(errors))


def plugin_sandbox_command(
    *, image: str, plugin: Path, harness: Path, structures: Path, output: Path
) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65532:65532",
        "--pids-limit",
        "256",
        "--memory",
        "16g",
        "--cpus",
        "8",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=1g",
        "--mount",
        f"type=bind,src={plugin.resolve()},dst=/work/plugin.py,readonly",
        "--mount",
        f"type=bind,src={harness.resolve()},dst=/opt/foundry/plugin_runner.py,readonly",
        "--mount",
        f"type=bind,src={structures.resolve()},dst=/inputs/structures,readonly",
        "--mount",
        f"type=bind,src={output.resolve()},dst=/output",
        image,
        "python",
        "/opt/foundry/plugin_runner.py",
        "--plugin",
        "/work/plugin.py",
        "--structures",
        "/inputs/structures",
        "--output",
        "/output",
    ]


def plugin_full_execution_command(
    *,
    image: str,
    plugin: Path,
    harness: Path,
    train_structures: Path,
    test_structures: Path,
    specification: Path,
    output: Path,
) -> list[str]:
    """Build the networkless full-matrix command owned by the trusted controller."""

    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65532:65532",
        "--pids-limit",
        "256",
        "--memory",
        "16g",
        "--cpus",
        "8",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=1g",
        "--mount",
        f"type=bind,src={plugin.resolve()},dst=/work/plugin.py,readonly",
        "--mount",
        f"type=bind,src={harness.resolve()},dst=/opt/foundry/plugin_runner.py,readonly",
        "--mount",
        f"type=bind,src={train_structures.resolve()},dst=/inputs/train,readonly",
        "--mount",
        f"type=bind,src={test_structures.resolve()},dst=/inputs/test,readonly",
        "--mount",
        f"type=bind,src={specification.resolve()},dst=/inputs/specification.json,readonly",
        "--mount",
        f"type=bind,src={output.resolve()},dst=/output",
        image,
        "python",
        "/opt/foundry/plugin_runner.py",
        "--plugin",
        "/work/plugin.py",
        "--output",
        "/output",
        "--mode",
        "full",
        "--train-structures",
        "/inputs/train",
        "--test-structures",
        "/inputs/test",
        "--specification",
        "/inputs/specification.json",
    ]
