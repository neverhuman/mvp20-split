"""Campaign Runtime's pure compiler boundary; compilation does not authorize execution."""

from .addresses import ActivationAddress
from .catalog import ResolvedTool, ToolCatalog
from .compiler import compile_campaign
from .errors import CompilationError
from .schemas import PinnedSchema, SchemaCatalog
from .shapes import SchemaIdentity

__all__ = ["ActivationAddress", "CompilationError", "PinnedSchema", "ResolvedTool", "SchemaCatalog", "SchemaIdentity", "ToolCatalog", "compile_campaign"]
