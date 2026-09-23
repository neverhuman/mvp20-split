"""amphora_benchkit -- shared performance kit for Amphora benchmark fires.

DETERMINISM CONTRACT
--------------------
Every public function in this package documents the ORIGINAL in-tree
implementation it was adopted from (file path + symbol) and is covered by a
pytest bit-identity test (benchkit/tests/) that executes the original code
verbatim (extracted from the original file's AST at test time -- never a
hand-copy) on in-tree canonical fixtures and asserts BYTE/BIT equality of
results (`==` on floats, `.tobytes()` on arrays), not approximate closeness.
The kit is only trustworthy because it is provably output-identical.

Usable two ways:
  * pip install -e ./benchkit
  * sys.path.insert(0, "./benchkit")

Modules:
  bootstrap   -- vectorized (cluster) bootstrap resampling
  linalg      -- Markov-chain ARL via np.linalg.solve (vs hand-rolled Gauss-Jordan)
  quadrature  -- batched stacked-solve ARL quadrature over (U, W) grids
  similarity  -- RDKit BulkTanimotoSimilarity wrappers (imported lazily)
  timing      -- wall_seconds decorator / contextmanager for diagnostics dicts
  origins     -- AST extraction of original in-tree code for bit-identity tests
"""

import os
from pathlib import Path

TREE_ROOT = str(
    Path(os.environ.get("AMPHORA_ROOT", Path(__file__).resolve().parents[2])).resolve()
)

from . import bootstrap, linalg, quadrature, timing, origins  # noqa: E402,F401

# similarity imports rdkit lazily inside functions; safe to import the module
from . import similarity  # noqa: E402,F401

__version__ = "0.1.0"
