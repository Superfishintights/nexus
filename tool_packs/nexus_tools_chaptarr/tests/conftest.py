"""Run the pack's tests from its source checkout without installing the pack."""
from pathlib import Path
import sys

PACK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACK_ROOT.parents[1]
for directory in (REPO_ROOT, PACK_ROOT):
    sys.path.insert(0, str(directory))
