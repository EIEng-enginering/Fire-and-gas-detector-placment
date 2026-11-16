"""Candidate compatibility entry; never recreate or overwrite the WP01 archive."""
from build_return_pack import build
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
print(json.dumps(build(root.parent/'FG_MAPPING_RETURN_REV_E_20261116.zip'),indent=2))
