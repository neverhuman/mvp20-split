from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from pandas import DataFrame
from pymatgen.core import Structure

from .kernels import KERNEL_OPERATIONS, PrimitiveCache, canonical_structure
from .schemas import SchemaError, expand_feature_spec


@dataclass(frozen=True)
class CompiledFamily:
    card: dict[str, Any]
    spec: dict[str, Any]
    columns: tuple[dict[str, Any], ...]

    @property
    def family_slug(self) -> str:
        return str(self.card["family_slug"])


class TrustedCompiler:
    def __init__(self, cache: PrimitiveCache | None = None):
        self.cache = cache or PrimitiveCache()
        self._feature_ids: set[str] = set()

    def compile(
        self,
        card: dict[str, Any],
        spec: dict[str, Any],
        *,
        source_role_id: str = "controller",
    ) -> CompiledFamily:
        rows = expand_feature_spec(card, spec, source_role_id=source_role_id)
        if spec["kernel"] == "custom":
            raise SchemaError(["custom specs must be executed by the sandbox plugin lane"])
        approved = set(KERNEL_OPERATIONS[spec["kernel"]])
        errors = [
            f"unsupported {spec['kernel']} operation: {row['operation']}"
            for row in rows
            if row["operation"] not in approved
        ]
        duplicates = sorted({row["feature_id"] for row in rows} & self._feature_ids)
        if duplicates:
            errors.append(f"controller feature IDs already compiled: {duplicates}")
        if errors:
            raise SchemaError(errors)
        self._feature_ids.update(row["feature_id"] for row in rows)
        return CompiledFamily(card=card, spec=spec, columns=tuple(rows))

    def compute_family(
        self, compiled: CompiledFamily, structure: Structure
    ) -> dict[str, float]:
        by_configuration: dict[str, dict[str, float]] = {}
        output: dict[str, float] = {}
        canonical = canonical_structure(structure)
        for column in compiled.columns:
            configuration = column["configuration"]
            key = repr(sorted(configuration.items()))
            if key not in by_configuration:
                by_configuration[key] = self.cache.compute(
                    column["kernel"], structure, configuration
                )
            value = float(by_configuration[key][column["operation"]])
            aggregation = column["aggregation"]
            if aggregation == "raw":
                pass
            elif aggregation in {"per-atom", "per-primitive-site"}:
                value /= max(len(canonical), 1)
            elif aggregation == "volume-normalized":
                value /= max(float(canonical.volume), 1e-12)
            else:
                raise ValueError(f"unsupported trusted-kernel aggregation: {aggregation}")
            output[column["feature_id"]] = value
        return output

    def compute_matrix(
        self,
        compiled: CompiledFamily,
        structures: Iterable[Structure],
        row_ids: Iterable[int | str],
    ) -> DataFrame:
        identifiers = list(row_ids)
        rows = [self.compute_family(compiled, structure) for structure in structures]
        if len(rows) != len(identifiers):
            raise ValueError("structure and row-ID counts differ")
        return DataFrame(rows).assign(id=identifiers)[
            ["id", *(column["feature_id"] for column in compiled.columns)]
        ]
