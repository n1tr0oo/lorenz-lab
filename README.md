# Lorenz Lab

Lorenz Lab is a small Python module for calculating and exporting trajectories of
the Lorenz system. It provides a numerical core, a command-line interface, black
and white plots, and a manifest recording each run's settings and file checksums.

The module supports the numerical foundation of an educational Lorenz platform.
It does not train ML models, classify regimes, assess learning outcomes, or provide
a web service. A plotted trajectory is not evidence that a model can predict chaos.

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
`docs/validation.json`. A local pass is not a GitHub Actions run.

## Repository structure

- `src/lorenz_lab/core.py`: configuration, equations, and integration.
- `src/lorenz_lab/export.py`: CSV, figures, environment record, and SHA-256 checksums.
- `src/lorenz_lab/cli.py`: JSON input and command-line errors.
- `tests/`: numerical and integration tests.
- `examples/default.json`: documented example configuration.
- `.github/workflows/ci.yml`: checks and versioned package delivery.
- `.github/ISSUE_TEMPLATE/`: reproducible defect reports.
- `docs/issues/`: follow-up tasks prepared for the repository issue tracker.
- `tools/publish_github.py`: publication through an authenticated GitHub CLI.

## Git and CI/CD

Use short feature branches and merge reviewed changes into `main`. Keep generated
bulk results, environments, and credentials out of source control. Small example
figures and validation records belong in documentation.

The workflow runs on pull requests to `main`, pushes to `main`, version tags, and
manual dispatch. Its Python 3.11/3.12 matrix runs syntax checks, tests, the example,
and wheel builds. A successful Python 3.12 job retains the wheel and example
outputs as an Actions artifact. A version tag matching `pyproject.toml` publishes
the checked wheel as a GitHub release after both matrix jobs pass.

This is package delivery. It does not deploy a hosted application or publish to
PyPI. The release job alone has write permission; ordinary checks have read-only
repository permission.

## Public GitHub submission

The authoritative publication state is `docs/publication.json`. It must contain
the actual public repository and workflow URLs before submission. No GitHub URL
or successful remote run is assumed from the presence of workflow files.

If using the supplied source package, restore its commit history first:

```bash
git clone repository.bundle lorenz-lab
cd lorenz-lab
```

With GitHub CLI installed and signed into the intended personal account:

```bash
gh auth login
python tools/publish_github.py --name lorenz-lab
```

The helper creates a new public repository, pushes the existing history, and
creates the three documented follow-up issues. It refuses to run if an `origin`
remote already exists. It records the real repository and workflow links. Check
the Actions run after publication; remote runner results must be recorded
separately from local validation. The tag can be pushed with
`git push origin v0.1.0` after the first hosted checks pass.

## License

MIT. Copyright 2026 Makhan Azat. See `LICENSE`.
