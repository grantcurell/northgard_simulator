import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import northgard.gpu_ops  # noqa: F401 — full suite requires a working CUDA GPU
