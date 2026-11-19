"""Validation test for generated gallery trajectory assets."""

import json
from pathlib import Path


def test_gallery_trajectories_asset_integrity():
    repo_root = Path(__file__).resolve().parent.parent
    data_file = repo_root / "frontend" / "src" / "data" / "gallery_trajectories.json"

    assert data_file.exists(), f"Gallery data file missing at: {data_file}"

    with open(data_file, "r", encoding="utf-8") as f:
        gallery = json.load(f)

    expected_presets = [
        "schwarzschild_isco_circular",
        "schwarzschild_precession",
        "schwarzschild_photon_sphere",
        "kerr_equatorial_prograde_photon",
        "kerr_equatorial_retrograde_photon",
        "kerr_circular_timelike",
        "kerr_equatorial_scattering",
    ]

    assert len(gallery) == 7
    for pid in expected_presets:
        assert pid in gallery, f"Preset {pid} missing from gallery JSON"
        item = gallery[pid]
        meta = item["metadata"]
        sim = item["simulation"]

        assert meta["id"] == pid
        assert sim["status"] == "completed"
        assert len(sim["config_hash"]) == 64

        coords = sim["trajectory"]["coordinates"]
        assert len(coords["r"]) > 0
        assert len(coords["theta"]) == len(coords["r"])
        assert len(coords["phi"]) == len(coords["r"])
        assert len(sim["trajectory"]["lambdas"]) == len(coords["r"])

        # Conserved quantities check
        cq = sim["conserved_quantities"]
        assert "energy" in cq
        assert "angular_momentum" in cq
        assert "hamiltonian_drift_max" in cq
        assert cq["hamiltonian_drift_max"] < 1e-10

        # Solver diagnostics check
        sd = sim["solver_diagnostics"]
        assert sd["method"] == "DOP853"
        assert sd["nfev"] > 0
