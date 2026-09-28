"""Static dependency guard: production owners consume only declared public contracts."""

import ast
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
THIRD_PARTY = {"pydantic": "pydantic", "fastapi": "fastapi", "uvicorn": "uvicorn", "sqlalchemy": "sqlalchemy", "psycopg": "psycopg", "alembic": "alembic", "jsonschema": "jsonschema"}


def project_specs(root: Path = ROOT):
    for parent in (root / "contracts", root / "services", root / "tools", root / "sdk"):
        if parent.exists():
            for manifest in sorted(parent.glob("*/pyproject.toml")):
                config = tomllib.loads(manifest.read_text(encoding="utf-8"))
                modules = list((manifest.parent / "src").iterdir())
                modules = [m.name for m in modules if m.is_dir() and not m.name.startswith(".")]
                if len(modules) != 1:
                    raise ValueError(f"Expected one owning import root: {manifest}")
                yield manifest.parent, config, modules[0]


def source_violations(
    source: str, owner: str, contracts: set[str], dependencies: set[str], public_dependencies: set[str]
) -> list[str]:
    errors = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                errors.append("dynamic_import")
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "import_module",
                "exec_module",
                "spec_from_file_location",
            }:
                errors.append("dynamic_import")
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute):
                if (
                    isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "sys"
                    and node.func.value.attr == "path"
                ):
                    errors.append("path_injection")
        if isinstance(node, ast.ImportFrom):
            if node.level:
                continue
            names = [node.module or ""]
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        else:
            continue
        for name in names:
            base = name.split(".")[0]
            if base == owner or base in sys.stdlib_module_names or base == "__future__":
                continue
            distribution = base.replace("_", "-")
            if base in contracts:
                if name != base:
                    errors.append("private_contract_import")
                if distribution not in dependencies or distribution not in public_dependencies:
                    errors.append("undeclared_contract_dependency")
            elif base in THIRD_PARTY and THIRD_PARTY[base] in dependencies:
                continue
            else:
                errors.append("undeclared_or_private_dependency")
    return errors


def check(root: Path = ROOT) -> list[str]:
    specs = list(project_specs(root))
    contracts = {module for path, cfg, module in specs if path.parent.name == "contracts"
                 or (path.parent.name == "sdk" and cfg.get("tool", {}).get("amphora", {}).get("public-client") is True)}
    edges = {}
    errors = []
    for path, config, owner in specs:
        dependencies = {
            dep.split(";")[0].split("[")[0].split("=")[0].split(">")[0].split("<")[0].strip()
            for dep in config["project"]["dependencies"]
        }
        public = set(config.get("tool", {}).get("amphora", {}).get("public-imports", []))
        edges[config["project"]["name"]] = public
        for source in sorted((path / "src").rglob("*.py")):
            for finding in source_violations(
                source.read_text(encoding="utf-8"), owner, contracts, dependencies, public
            ):
                errors.append(f"{source.relative_to(root)}: {finding}")

    def visit(name, stack):
        if name in stack:
            errors.append("dependency_cycle: " + " -> ".join((*stack, name)))
            return
        for child in edges.get(name, set()):
            visit(child, (*stack, name))

    for name in edges:
        visit(name, ())
    return errors


if __name__ == "__main__":
    findings = check()
    if findings:
        raise SystemExit("\n".join(findings))
    print("Production dependency boundaries verified")
