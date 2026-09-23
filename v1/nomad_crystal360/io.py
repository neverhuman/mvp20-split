from __future__ import annotations

from pathlib import Path

import pandas as pd
from pymatgen.core import Lattice, Structure

from .constants import ELEMENTS


def read_geometry(path: Path) -> Structure:
    """Read a NOMAD ``geometry.xyz`` file into a wrapped periodic structure."""
    lattice: list[list[float]] = []
    species: list[str] = []
    cart_coords: list[list[float]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            parts = raw_line.split()
            if not parts or parts[0].startswith("#"):
                continue
            if parts[0] == "lattice_vector":
                lattice.append([float(value) for value in parts[1:4]])
            elif parts[0] == "atom":
                symbol = parts[4]
                if symbol not in ELEMENTS:
                    raise ValueError(f"Unexpected element {symbol!r} in {path}")
                cart_coords.append([float(value) for value in parts[1:4]])
                species.append(symbol)
    if len(lattice) != 3:
        raise ValueError(f"Expected three lattice vectors in {path}, found {len(lattice)}")
    if not species:
        raise ValueError(f"No atoms found in {path}")
    return Structure(
        Lattice(lattice),
        species,
        cart_coords,
        coords_are_cartesian=True,
        to_unit_cell=True,
    )


def load_structures(frame: pd.DataFrame, geometry_root: Path) -> list[Structure]:
    structures: list[Structure] = []
    for row in frame.itertuples(index=False):
        structure_id = int(getattr(row, "id"))
        structure = read_geometry(geometry_root / str(structure_id) / "geometry.xyz")
        expected = int(round(float(getattr(row, "number_of_total_atoms"))))
        if len(structure) != expected:
            raise ValueError(
                f"Geometry atom count mismatch for id={structure_id}: "
                f"csv={expected}, geometry={len(structure)}"
            )
        structures.append(structure)
    return structures
