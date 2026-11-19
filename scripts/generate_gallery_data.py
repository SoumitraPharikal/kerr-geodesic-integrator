"""Reproducible trajectory generation script for Kerr Geodesics Lab Gallery.

Calls the authoritative Python engine through the stateless service adapter
to compute and serialize real numerical trajectories for all 7 registered presets.
Outputs to frontend/src/data/gallery_trajectories.json.
"""

import json
import sys
from pathlib import Path

# Add src to sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from geodesics.api.schemas import SimulationRequest
from geodesics.api.service import PRESET_METADATA_CATALOGUE, run_simulation


def generate_all_presets():
    output_dir = repo_root / "frontend" / "src" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "gallery_trajectories.json"

    gallery_data = {}

    print(f"Generating trajectories for {len(PRESET_METADATA_CATALOGUE)} presets...")

    for preset in PRESET_METADATA_CATALOGUE:
        print(f" -> Integrating preset: {preset.id} ({preset.name})")
        req = SimulationRequest(
            preset_id=preset.id,
            parameters=dict(preset.default_parameters),
        )
        resp = run_simulation(req)
        resp_dict = resp.model_dump()

        gallery_data[preset.id] = {
            "metadata": {
                "id": preset.id,
                "name": preset.name,
                "description": preset.description,
                "spacetime": preset.spacetime,
                "geodesic_type": preset.geodesic_type,
                "default_parameters": preset.default_parameters,
            },
            "simulation": resp_dict,
        }

        print(
            f"    Status: {resp.status}, Samples: {len(resp.trajectory.lambdas)}, "
            f"Config Hash: {resp.config_hash[:16]}..., Drift: {resp.conserved_quantities.hamiltonian_drift_max:.2e}"
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(gallery_data, f, indent=2)

    print(f"\nSuccessfully written verified trajectory data to:\n  {output_file}")


if __name__ == "__main__":
    generate_all_presets()
