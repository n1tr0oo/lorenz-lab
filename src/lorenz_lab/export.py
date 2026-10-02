"""Complete result directories with raw arrays, plots and provenance."""

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import __version__
from .core import Result


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_commit():
    value = os.environ.get("LORENZ_SOURCE_COMMIT", "")
    if len(value) == 40 and all(c in "0123456789abcdef" for c in value.lower()):
        return value.lower()
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
            capture_output=True, text=True, check=True, timeout=3,
        )
        return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def export_result(result: Result, destination) -> Path:
    """Refuse overwrites and publish a directory only after all files exist."""
    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"output already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".lorenz-stage-", dir=target.parent))
    try:
        data = np.column_stack([result.time, result.state])
        np.savetxt(stage / "trajectory.csv", data, delimiter=",",
                   header="t,x,y,z", comments="", fmt="%.17e")
        mask = result.time >= result.config.transient
        with plt.rc_context({"font.family": "serif", "font.size": 11}):
            fig, ax = plt.subplots(figsize=(8, 3.4))
            for i, (label, style) in enumerate(zip(["x", "y", "z"], ["-", "--", ":"])):
                ax.plot(result.time[mask], result.state[mask, i], style,
                        color="black", linewidth=0.8, label=label)
            ax.set(xlabel="Time (model units)", ylabel="State (dimensionless)")
            ax.legend(frameon=False, ncol=3)
            ax.grid(color="0.85", linewidth=0.4)
            fig.tight_layout()
            fig.savefig(stage / "time_series.png", dpi=160)
            plt.close(fig)
            fig = plt.figure(figsize=(6, 4.8))
            ax = fig.add_subplot(111, projection="3d")
            ax.plot(*result.state[mask].T, color="black", linewidth=0.55)
            ax.set(xlabel="x", ylabel="y", zlabel="z")
            ax.set_title("Lorenz trajectory after transient removal")
            fig.tight_layout()
            fig.savefig(stage / "phase_portrait.png", dpi=160)
            plt.close(fig)
        artifacts = {name: checksum(stage / name) for name in
                     ["trajectory.csv", "time_series.png", "phase_portrait.png"]}
        manifest = {
            "schema_version": 1, "module_version": __version__,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "source_commit": source_commit(), "config": asdict(result.config),
            "solver": "DOP853", "solver_completed": True,
            "samples": len(result.time), "rhs_evaluations": result.evaluations,
            "effective_sample_step": float(result.time[1] - result.time[0]),
            "transient_applies_to": "plots only; CSV retains every sample",
            "environment": {"python": platform.python_version(),
                            "platform": platform.platform(),
                            **{p: importlib.metadata.version(p)
                               for p in ["numpy", "scipy", "matplotlib"]}},
            "sha256": artifacts,
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        # Recheck immediately before publication; the CLI is a single-user tool.
        if target.exists():
            raise FileExistsError(f"output already exists: {target}")
        stage.rename(target)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return target
