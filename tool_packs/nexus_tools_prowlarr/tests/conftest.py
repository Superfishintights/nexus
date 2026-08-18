from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ROOT = Path(__file__).resolve().parents[1]

for path in (REPO_ROOT, PACK_ROOT):
    path_s = str(path)
    if path_s not in sys.path:
        sys.path.insert(0, path_s)
