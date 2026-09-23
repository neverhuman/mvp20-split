from __future__ import annotations

import ast
import hashlib
import io
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any


ALLOWED_IMPORTS = {
    "argparse",
    "ase",
    "collections",
    "dscribe",
    "functools",
    "gudhi",
    "itertools",
    "json",
    "math",
    "matminer",
    "networkx",
    "numpy",
    "pandas",
    "pathlib",
    "pymatgen",
    "scipy",
    "spglib",
    "statistics",
    "typing",
}
FORBIDDEN_CALLS = {"compile", "eval", "exec", "__import__", "breakpoint"}
FORBIDDEN_NAMES = {"os", "socket", "subprocess", "requests", "urllib", "httpx", "ftplib"}
MAX_ARCHIVE_FILES = 100
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


def static_check_generator(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [f"syntax error: {error.msg} at line {error.lineno}"]
    errors: list[str] = []
    has_featurizer = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            for name in names:
                root = name.split(".", 1)[0]
                if root not in ALLOWED_IMPORTS:
                    errors.append(f"import is not allowed: {name}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                errors.append(f"call is not allowed: {node.func.id}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            errors.append(f"name is not allowed: {node.id}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            errors.append(f"{type(node).__name__.lower()} declarations are not allowed")
        elif isinstance(node, ast.FunctionDef) and node.name == "featurize_structure":
            has_featurizer = True
    if not has_featurizer:
        errors.append("generator must define featurize_structure(structure)")
    return sorted(set(errors))


def safe_extract_tar_bytes(data: bytes, destination: Path) -> list[Path]:
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError("archive exceeds the compressed size limit")
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    total = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError("archive contains too many entries")
        for member in members:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts:
                raise ValueError(f"unsafe archive path: {member.name}")
            if not member.isfile():
                raise ValueError(f"archive entry must be a regular file: {member.name}")
            total += member.size
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("archive exceeds the uncompressed size limit")
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and (target.is_symlink() or not target.is_file()):
                raise ValueError(f"refusing to overwrite unsafe path: {target}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"cannot read archive entry: {member.name}")
            temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            temporary.write_bytes(source.read())
            os.replace(temporary, target)
            extracted.append(target)
    return extracted


def docker_sandbox_command(
    *,
    image: str,
    generator: Path,
    harness: Path,
    public_inputs: Path,
    train_geometry: Path,
    test_geometry: Path,
    output: Path,
    real_sample_id: int,
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
        f"type=bind,src={generator.resolve()},dst=/work/generator.py,readonly",
        "--mount",
        f"type=bind,src={harness.resolve()},dst=/opt/foundry/sandbox_runner.py,readonly",
        "--mount",
        f"type=bind,src={public_inputs.resolve()},dst=/inputs,readonly",
        "--mount",
        f"type=bind,src={train_geometry.resolve()},dst=/inputs/train_geometry,readonly",
        "--mount",
        f"type=bind,src={test_geometry.resolve()},dst=/inputs/test_geometry,readonly",
        "--mount",
        f"type=bind,src={output.resolve()},dst=/output",
        image,
        "python",
        "/opt/foundry/sandbox_runner.py",
        "--generator",
        "/work/generator.py",
        "--inputs",
        "/inputs",
        "--output",
        "/output",
        "--real-sample-id",
        str(real_sample_id),
    ]


def value_hash(values: Any) -> str:
    try:
        data = values.tobytes(order="C")
    except AttributeError:
        data = repr(values).encode()
    return hashlib.sha256(data).hexdigest()
