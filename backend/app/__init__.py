"""LunaScope Backend Package."""
from pathlib import Path
import sys
# Optional checkout-local dependencies; normal installations use requirements.txt.
_local=Path(__file__).resolve().parents[2]/'.science-deps'
if _local.is_dir():sys.path.append(str(_local))
