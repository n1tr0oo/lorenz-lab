import math
import unittest

import numpy as np

from lorenz_lab.core import Config, SimulationError, lorenz_rhs, simulate


class ConfigurationTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        self.assertEqual(Config().initial, (1.0, 1.0, 1.0))

    def test_rejects_nonfinite_scalar(self):
        for value in [math.nan, math.inf, -math.inf]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                Config(rho=value)

    def test_rejects_invalid_parameter_bounds(self):
        for data in [{"sigma": 0}, {"sigma": 101}, {"rho": -1}, {"rho": 201},
                     {"beta": -1}, {"beta": 51}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                Config(**data)

    def test_rejects_boolean(self):
        with self.assertRaises(ValueError):
            Config(sigma=True)

    def test_rejects_wrong_state_shape(self):
        for state in [(1, 2), "123", (1, 2, 3, 4)]:
            with self.subTest(state=state), self.assertRaises(ValueError):
                Config(initial=state)

    def test_rejects_invalid_state_values(self):
        for state in [(1, math.nan, 1), (1001, 0, 0), (1, True, 0)]:
            with self.subTest(state=state), self.assertRaises(ValueError):
                Config(initial=state)

    def test_rejects_sampling_budget(self):
        with self.assertRaises(ValueError):
            Config(duration=50, sample_step=0.0001)

    def test_rejects_invalid_transient(self):
        for transient in [-1, 30, math.inf]:
            with self.subTest(transient=transient), self.assertRaises(ValueError):
                Config(transient=transient)

    def test_rejects_tolerance_outside_policy(self):
        with self.assertRaises(ValueError):
            Config(rtol=1e-15)


class NumericalTests(unittest.TestCase):
    def test_known_derivative(self):
        np.testing.assert_allclose(lorenz_rhs(0, [1, 2, 3], 10, 28, 2), [10, 23, -4])

    def test_origin_is_stationary(self):
        result = simulate(Config(initial=(0, 0, 0), duration=1, transient=0))
        np.testing.assert_array_equal(result.state, np.zeros_like(result.state))

    def test_nonzero_equilibrium(self):
        x = math.sqrt((8 / 3) * 27)
        initial = (x, x, 27)
        result = simulate(Config(initial=initial, duration=1, transient=0))
        np.testing.assert_allclose(result.state, np.tile(initial, (101, 1)), atol=1e-9)

    def test_exact_exponential_solution(self):
        result = simulate(Config(initial=(0, 0, 2), duration=1, transient=0))
        np.testing.assert_allclose(result.state[:, 2], 2 * np.exp(-(8 / 3) * result.time),
                                   rtol=2e-8, atol=1e-10)

    def test_symmetry(self):
        a = simulate(Config(duration=1, transient=0, initial=(1, 2, 3)))
        b = simulate(Config(duration=1, transient=0, initial=(-1, -2, 3)))
        np.testing.assert_allclose(b.state, a.state * [-1, -1, 1], rtol=1e-7, atol=1e-8)

    def test_short_horizon_convergence(self):
        a = simulate(Config(duration=1, transient=0, rtol=1e-7, atol=1e-9))
        b = simulate(Config(duration=1, transient=0, rtol=1e-10, atol=1e-12))
        self.assertLess(float(np.max(np.abs(a.state - b.state))), 1e-5)

    def test_output_grid_includes_endpoints(self):
        result = simulate(Config(duration=1, sample_step=0.03, transient=0))
        self.assertEqual(result.time[0], 0)
        self.assertEqual(result.time[-1], 1)
        self.assertLessEqual(np.max(np.diff(result.time)), 0.03)
        self.assertEqual(result.state.shape, (35, 3))

    def test_evaluation_budget_stops_calculation(self):
        with self.assertRaisesRegex(SimulationError, "budget"):
            simulate(Config(duration=1, transient=0), max_evaluations=2)

    def test_state_limit_stops_calculation(self):
        with self.assertRaisesRegex(SimulationError, "state limit"):
            simulate(Config(duration=1, transient=0), state_limit=2)

    def test_nonconfig_is_rejected(self):
        with self.assertRaises(TypeError):
            simulate({})


if __name__ == "__main__":
    unittest.main()
