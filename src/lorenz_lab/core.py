"""Validated configuration and numerical integration, independent of plotting."""

from dataclasses import dataclass
import math

import numpy as np
from scipy.integrate import solve_ivp


class SimulationError(RuntimeError):
    """The solver did not produce a complete, finite trajectory."""


@dataclass(frozen=True)
class Config:
    sigma: float = 10.0
    rho: float = 28.0
    beta: float = 8.0 / 3.0
    initial: tuple[float, float, float] = (1.0, 1.0, 1.0)
    duration: float = 30.0
    sample_step: float = 0.01
    transient: float = 5.0
    rtol: float = 1e-9
    atol: float = 1e-11

    def __post_init__(self):
        bounds = {
            "sigma": (0, 100, False), "rho": (0, 200, True),
            "beta": (0, 50, False), "duration": (0, 50, False),
            "sample_step": (1e-4, 0.25, True),
            "rtol": (1e-12, 1e-3, True), "atol": (1e-14, 1e-3, True),
        }
        for name, (low, high, include_low) in bounds.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name} must be a finite number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be a finite number")
            if value > high or (value < low if include_low else value <= low):
                sign = "<=" if include_low else "<"
                raise ValueError(f"{name} must satisfy {low} {sign} value <= {high}")
        if (isinstance(self.transient, bool)
                or not isinstance(self.transient, (int, float))
                or not math.isfinite(self.transient)
                or not 0 <= self.transient < self.duration):
            raise ValueError("transient must satisfy 0 <= transient < duration")
        if not isinstance(self.initial, (list, tuple)) or len(self.initial) != 3:
            raise ValueError("initial must contain three finite coordinates")
        for value in self.initial:
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or abs(value) > 1000):
                raise ValueError("initial coordinates must be finite and within [-1000, 1000]")
        object.__setattr__(self, "initial", tuple(float(v) for v in self.initial))
        if math.ceil(self.duration / self.sample_step) + 1 > 20001:
            raise ValueError("requested output exceeds the 20,001-sample budget")


@dataclass(frozen=True)
class Result:
    config: Config
    time: np.ndarray
    state: np.ndarray
    evaluations: int


def lorenz_rhs(_time, state, sigma, rho, beta):
    x, y, z = state
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])


def simulate(config: Config, *, max_evaluations=200000, state_limit=1e6) -> Result:
    """Integrate through the full horizon or raise without returning partial data.

    sample_step is a maximum output interval. The uniform grid includes both
    endpoints; its effective spacing is recorded by the export layer.
    """
    if not isinstance(config, Config):
        raise TypeError("config must be a Config instance")
    if (isinstance(max_evaluations, bool) or not isinstance(max_evaluations, int)
            or not 1 <= max_evaluations <= 200000):
        raise ValueError("max_evaluations must be an integer in [1, 200000]")
    if not math.isfinite(state_limit) or not 1 <= state_limit <= 1e6:
        raise ValueError("state_limit must be within [1, 1000000]")
    if np.max(np.abs(config.initial)) >= state_limit:
        raise SimulationError("initial state reaches the configured state limit")
    count = 0

    def rhs(time, state):
        nonlocal count
        count += 1
        if count > max_evaluations:
            raise SimulationError("right-hand-side evaluation budget exhausted")
        if not np.all(np.isfinite(state)):
            raise SimulationError("nonfinite state encountered")
        derivative = lorenz_rhs(time, state, config.sigma, config.rho, config.beta)
        if not np.all(np.isfinite(derivative)):
            raise SimulationError("nonfinite derivative encountered")
        return derivative

    def boundary(_time, state):
        return state_limit - np.max(np.abs(state))

    boundary.terminal = True
    boundary.direction = -1
    intervals = math.ceil(config.duration / config.sample_step)
    times = np.linspace(0, config.duration, intervals + 1)
    solution = solve_ivp(
        rhs, (0, config.duration), config.initial, method="DOP853", t_eval=times,
        rtol=config.rtol, atol=config.atol, events=boundary,
    )
    if not solution.success:
        raise SimulationError(f"solver failed: {solution.message}")
    if solution.status == 1 or len(solution.t) != len(times):
        raise SimulationError("state limit reached before the requested horizon")
    state = solution.y.T
    if not np.all(np.isfinite(state)) or np.max(np.abs(state)) >= state_limit:
        raise SimulationError("invalid or out-of-bounds trajectory")
    return Result(config, solution.t, state, count)
