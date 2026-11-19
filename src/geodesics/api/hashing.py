"""Deterministic canonical configuration hashing for Kerr Geodesics Lab.

Computes deterministic SHA-256 digests over validated preset IDs and parameter
dictionaries to provide reproducible, collision-resistant configuration identifiers.

Serialization Specification
---------------------------
- Lexicographical Sorting: Keys are sorted lexicographically at all nesting levels.
- Minimal Separators: No extraneous whitespace (',' and ':').
- Machine-Precision Floats: Floating point numbers are preserved in their exact
  IEEE 754 64-bit binary representation via Python's standard shortest round-tripping
  decimal serializer (dtoa). No arbitrary precision truncation or decimal rounding
  is applied, preventing artificial collisions between nearby distinct parameters.
- Default Normalization: Pydantic schemas normalize defaults prior to serialization,
  ensuring that omitting a default parameter produces an identical hash to providing
  that default explicitly.
- Encoding & Digest: Serialized canonical JSON strings are UTF-8 encoded and digested
  with SHA-256.

Note on RFC 8785: This scheme uses Python's deterministic JSON serialization.
While it achieves lexicographical key ordering and shortest float representations,
it formats integer-valued floats with a trailing '.0' (e.g., 1.0) rather than as
integers (e.g., 1), conforming to Python/Pydantic typed float representations.
"""

import hashlib
import json
from typing import Any, Dict


def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """Serializes a dictionary into canonical UTF-8 encoded JSON bytes.

    - Keys are sorted lexicographically at all nesting levels.
    - Floating point values are preserved at full IEEE 754 double precision without
      lossy decimal rounding.
    - Whitespace separators are minimal (',', ':').
    """

    def normalize_item(item: Any) -> Any:
        if isinstance(item, dict):
            return {k: normalize_item(item[k]) for k in sorted(item.keys())}
        elif isinstance(item, (list, tuple)):
            return [normalize_item(x) for x in item]
        elif isinstance(item, float):
            return item
        elif isinstance(item, (int, str, bool)) or item is None:
            return item
        else:
            return str(item)

    normalized = normalize_item(data)
    json_str = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return json_str.encode("utf-8")


def compute_simulation_config_hash(preset_id: str, parameters: Dict[str, Any]) -> str:
    """Computes a deterministic SHA-256 hash for a simulation preset and its parameters."""
    payload = {
        "preset_id": preset_id,
        "parameters": parameters,
    }
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return digest


def compute_shadow_config_hash(
    mass: float, spin: float, observer_inclination: float, num_points: int
) -> str:
    """Computes a deterministic SHA-256 hash for a shadow configuration."""
    payload = {
        "mass": mass,
        "spin": spin,
        "observer_inclination": observer_inclination,
        "num_points": num_points,
    }
    digest = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return digest
