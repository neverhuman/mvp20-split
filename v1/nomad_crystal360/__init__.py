"""NOMAD Crystal360 physically interpretable feature package."""

__all__ = ["Crystal360Featurizer", "Crystal360Schema", "build_primary_definitions"]
__version__ = "1.0.0"

def __getattr__(name):
    # Keep feature-only CUDA workers usable in the lightweight pinned ML
    # environment, which intentionally does not install pymatgen/spglib.
    if name == "Crystal360Featurizer":
        from .featurizer import Crystal360Featurizer
        return Crystal360Featurizer
    if name in ("Crystal360Schema", "build_primary_definitions"):
        from .schema import Crystal360Schema, build_primary_definitions
        return {"Crystal360Schema": Crystal360Schema, "build_primary_definitions": build_primary_definitions}[name]
    raise AttributeError(name)
