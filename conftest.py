import sys
from pathlib import Path

# Tests import src.* / shared.* directly, so the repo root has to be importable.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
