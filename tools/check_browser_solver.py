"""Compare the browser RK4 with independent SciPy DOP853 on a short horizon."""
import json
import os
from pathlib import Path
import subprocess

import numpy as np
from scipy.integrate import solve_ivp

root = Path(__file__).resolve().parents[1]
node = os.getenv("LORENZ_NODE", "node")
base = {"sigma": 10, "rho": 28, "beta": 8 / 3, "duration": 1,
        "sample_step": 0.01, "transient": 0, "initial": [1, 1, 1]}


def browser(config, max_step=0.001):
    p = subprocess.run([node, str(root / "tools/browser_reference.mjs")],
                       input=json.dumps({"config": config, "maxStep": max_step}),
                       text=True, capture_output=True, check=True)
    return np.array(json.loads(p.stdout)["values"]).reshape(-1, 4)


records = []
for initial, rho in [([1, 1, 1], 28), ([-1, -1, 1], 28),
                     ([0, 0, 1], 28), ([1, 1, 1], 0.5)]:
    config = {**base, "initial": initial, "rho": rho}
    actual = browser(config)

    def rhs(t, state):
        x, y, z = state
        return [config["sigma"] * (y - x), x * (rho - z) - y,
                x * y - config["beta"] * z]

    reference = solve_ivp(rhs, (0, 1), initial, method="DOP853",
                          t_eval=actual[:, 0], rtol=1e-12, atol=1e-14)
    assert reference.success
    error = float(np.max(np.abs(actual[:, 1:] - reference.y.T)))
    assert error < 2e-6, error
    records.append({"initial": initial, "rho": rho, "max_abs_error": error})
    if initial == [1, 1, 1] and rho == 28:
        refined = browser(config, 0.0005)
        refined_error = float(np.max(np.abs(refined[:, 1:] - reference.y.T)))
        assert refined_error < error / 8, (error, refined_error)
        records[-1]["half_step_max_abs_error"] = refined_error

print(json.dumps({"short_horizon": 1, "acceptance_max_abs_error": 2e-6,
                  "cases": records, "passed": True}, indent=2))
