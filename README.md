# Lorenz Lab

Lorenz Lab is a small Python module for calculating and exporting trajectories of
the Lorenz system. It provides a numerical core, a command-line interface, black
and white plots, and a manifest recording each run's settings and file checksums.

The module supports the numerical foundation of an educational Lorenz platform.
It does not train ML models, classify regimes, assess learning outcomes, or provide
a Python web service. A browser demo is supplied in `docs/index.html`; its
calculation runs on the visitor's device. A plotted trajectory is not evidence
that a model can predict chaos.

## Browser demo

The GitHub Pages entry point is `docs/index.html`. It provides parameter inputs,
three phase-plane projections, time-series plots and CSV/JSON downloads.
No Python server, account or external plotting library is required.

The browser solver uses fixed-step RK4 with a maximum internal step of 0.001.
This differs from the Python module's adaptive DOP853 solver. Twelve Node tests
check numerical properties and validation. `tools/check_browser_solver.py`
compares four one-unit cases against independent SciPy DOP853 references with a
maximum absolute error below 2e-6 and checks improvement when the step is halved.
These short-horizon checks do not certify long chaotic pointwise agreement.

Browser initial coordinates are limited to -100 through 100. The UI terminates
a worker after eight seconds; cancellation retains the previous completed result.
CSV retains every sample, including the interval hidden on the charts. The JSON
export records settings, method, step and the CSV's SHA-256 checksum.

To preview locally, run `python -m http.server 8000 --directory docs` and open
`http://localhost:8000`. For Pages, select `main` and `/docs` as the publishing
source in the repository's Pages settings.

## Install and run

Use Python 3.11 or 3.12. The locally verified environment used Python 3.12.14.
From this repository's root, create a virtual environment and install the pinned
dependencies. Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
python -m lorenz_lab --config examples/default.json --output results/default
```

Linux or macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m lorenz_lab --config examples/default.json --output results/default
```

After installation, `lorenz-lab` is an equivalent console command. To see the
configuration defaults, run `python -m lorenz_lab --print-defaults`.

Each successful run creates `trajectory.csv`, `time_series.png`,
`phase_portrait.png`, and `manifest.json`. Choose a new output directory for each
run; the module refuses to overwrite existing results. The CSV contains every
sample, including the transient. Only the plots remove the configured transient.

## Parameters and computation limits

Edit a copy of `examples/default.json`. Coordinates and time are dimensionless
model quantities. `sample_step` specifies the maximum interval between output
samples, not the solver's internal step. The exported uniform grid includes both
endpoints, and its effective interval appears in the manifest.

| Input | Accepted range |
| --- | --- |
| sigma | Greater than 0, at most 100 |
| rho | 0 through 200 |
| beta | Greater than 0, at most 50 |
| initial coordinates | Three finite numbers, each within -1000 through 1000 |
| duration | Greater than 0, at most 50 model time units |
| sample_step | 0.0001 through 0.25; at most 20,001 output samples |
| transient | At least 0 and strictly smaller than duration |
| rtol | 1e-12 through 1e-3 |
| atol | 1e-14 through 1e-3 |

These are this module's input and resource policies, not the mathematical limits
of the Lorenz equations. Nonfinite inputs are rejected. Integration stops with an
error if a coordinate reaches magnitude 1,000,000, or if the right-hand side is
evaluated more than 200,000 times. No partial trajectory is exported as a success.
A hard wall-clock timeout would require a separate worker process; it is a
documented follow-up rather than a guarantee of this CLI.

## Validate and build

```bash
python -m compileall -q src tests
python -m unittest discover -s tests -v
python -m pip wheel --no-build-isolation --no-deps . --wheel-dir dist
```

The 26 test methods cover input validation, an exact exponential solution,
equilibria, Lorenz symmetry, short-horizon convergence, computation limits,
exports, checksums, and CLI behaviour. Tests use Python's `unittest` framework;
no separate test runner is required. Local validation evidence is recorded in
`docs/validation.json`. Both hosted Python jobs also passed all 26 methods;
the run and job evidence is recorded in `docs/hosted_ci.json`.

## Repository structure

- `src/lorenz_lab/core.py`: configuration, equations, and integration.
- `src/lorenz_lab/export.py`: CSV, figures, environment record, and SHA-256 checksums.
- `src/lorenz_lab/cli.py`: JSON input and command-line errors.
- `tests/`: numerical and integration tests.
- `examples/default.json`: documented example configuration.
- `.github/workflows/ci.yml`: checks and versioned package delivery.
- `.github/ISSUE_TEMPLATE/`: reproducible defect reports.
- `docs/issues/`: follow-up tasks prepared for the repository issue tracker.
- `docs/hosted_ci.json`: verified hosted tests, build and delivery artifact.
- `docs/history_import.json`: correspondence between local and public commits.
- `tools/publish_github.py`: optional publication helper for a new or empty repository.

## Git and CI/CD

Use short feature branches and merge reviewed changes into `main`. Keep generated
bulk results, environments, and credentials out of source control. Small example
figures and validation records belong in documentation.

The workflow runs on pull requests to `main`, pushes to `main`, version tags, and
manual dispatch. Its Python 3.11/3.12 matrix runs syntax checks, Python tests,
browser tests, the SciPy comparison, the example and wheel builds.
A successful Python 3.12 job retains the wheel and example
outputs as an Actions artifact. A version tag matching `pyproject.toml` publishes
the checked wheel as a GitHub release after both matrix jobs pass.

This is package delivery. It does not deploy a hosted application or publish to
PyPI. The release job alone has write permission; ordinary checks have read-only
repository permission.

## Public GitHub submission

The public repository is https://github.com/n1tr0oo/lorenz-lab.
The workflow is available at
https://github.com/n1tr0oo/lorenz-lab/blob/main/.github/workflows/ci.yml.
The verified run at
https://github.com/n1tr0oo/lorenz-lab/actions/runs/37061348092
passed on Python 3.11 and 3.12. Each job ran all 26 tests, executed the default
example and built the wheel. The Python 3.12 job retained `lorenz-delivery`.
This run was a push to `main`; the tag-triggered release job was skipped.

Clone the published project:

```bash
git clone https://github.com/n1tr0oo/lorenz-lab.git
cd lorenz-lab
```

If using the supplied source package, restore its commit history first:

```bash
git clone repository.bundle lorenz-lab
cd lorenz-lab
```

The bundle retains the original local development commits. The public history
reproduces their source trees and merge relationships with new commit metadata.
`docs/history_import.json` maps the local and public commit IDs.

The three follow-up tasks are tracked at:

- https://github.com/n1tr0oo/lorenz-lab/issues/1 — browser adapter.
- https://github.com/n1tr0oo/lorenz-lab/issues/2 — worker timeout.
- https://github.com/n1tr0oo/lorenz-lab/issues/3 — further portability checks.

`docs/publication.json` records the repository, workflow, verified run and issues.
Windows execution and a tagged release remain separate follow-up checks.

## License

MIT. Copyright 2026 Makhan Azat. See `LICENSE`.
