"""Verify raw outputs from two runs of the same built image without extra packages."""
import hashlib
import json
from pathlib import Path
import sys


def verify(first, second, commit):
    runs = [Path(first), Path(second)]
    manifests = []
    for run in runs:
        manifest = json.loads((run / "manifest.json").read_text())
        assert manifest["source_commit"] == commit, "source revision differs"
        assert manifest["solver_completed"] is True, "solver did not complete"
        assert manifest["samples"] == 3001, "unexpected default sample count"
        for name, expected in manifest["sha256"].items():
            assert hashlib.sha256((run / name).read_bytes()).hexdigest() == expected, name
        manifests.append(manifest)
    assert (runs[0] / "trajectory.csv").read_bytes() == (runs[1] / "trajectory.csv").read_bytes(), "raw trajectories differ"
    assert manifests[0]["config"] == manifests[1]["config"], "settings differ"
    assert manifests[0]["environment"] == manifests[1]["environment"], "environments differ"
    return {"passed": True, "source_commit": commit, "samples_per_run": 3001,
            "csv_byte_identical": True, "checksums_valid": True,
            "scope": "Two executions of one image on one runner; no cross-platform bitwise claim",
            "trajectory_sha256": manifests[0]["sha256"]["trajectory.csv"]}


if __name__ == "__main__":
    print(json.dumps(verify(*sys.argv[1:]), indent=2))
