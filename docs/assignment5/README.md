# Assignment 5 DevOps and CI/CD

This increment continues Lorenz Lab with Docker and a real Jenkins pipeline.
It uses the existing Python numerical module and its automated tests.

## Pipeline stages

1. Checkout the selected source revision.
2. Build the test target and execute the unit tests, exporting JUnit XML.
3. Build the runtime image and record its image ID and source label.
4. Execute the documented experiment twice. Check every exported checksum,
   source revision, environment and byte equality of the two raw CSV files.
5. Deploy the included browser demonstration in a temporary HTTP container and
   check its response. This is test deployment, not permanent LMS hosting.

`Jenkinsfile` contains the stages. `.github/workflows/jenkins.yml` provisions a
disposable Jenkins server on an Ubuntu GitHub Actions runner for each pushed
revision or pull request. Jenkins itself executes the stages and publishes the
test results and archived files. Actions supplies the host and retains evidence;
it is not a replacement for Jenkins in this implementation.

The temporary server listens only on the runner's loopback address. It is removed
after screenshots and artifacts are collected. No public Jenkins URL persists.
The existing GitHub Pages site remains at https://n1tr0oo.github.io/lorenz-lab/.

## Run the same Jenkins setup locally

Requirements: a disposable Linux host with Docker, Python 3, Internet access,
and no existing service on ports 8080 and 8090. On Windows, use Docker Desktop
with Linux containers and a Linux environment such as WSL2.

```bash
git clone https://github.com/n1tr0oo/lorenz-lab.git
cd lorenz-lab
git switch assignment-5-devops
LORENZ_REF=$(git rev-parse HEAD) python3 ci/run_jenkins.py
```

Then open http://127.0.0.1:8080/job/lorenz-lab/ and
http://127.0.0.1:8090/. The setup deliberately gives this local educational
controller access to the Docker daemon. Run it only on a disposable trusted host.
A shared installation requires authentication, isolated build agents and
controlled Docker access; do not expose this controller on a public interface.

```bash
docker rm -f lorenz-demo-1 lorenz-jenkins
docker volume rm lorenz-jenkins-home
```

## Run the application image directly

```bash
docker build --target runtime --build-arg SOURCE_COMMIT=$(git rev-parse HEAD) -t lorenz-lab:local .
docker run --name lorenz-example --cap-drop ALL --security-opt no-new-privileges lorenz-lab:local
docker cp lorenz-example:/data/default ./container-results
docker rm lorenz-example
```

Outputs include a raw CSV, two figures, and a JSON manifest with settings,
dependency versions, source revision and SHA-256 checksums. Compare two runs
using `python3 tools/verify_runs.py FIRST SECOND SOURCE_SHA`.

## Scope and limitations

No Docker Hub credentials are needed: registry publication is optional and is
not configured. Kubernetes deployment is also optional and is not claimed.
The test website is served automatically after the checks pass. It is removed
at the end of the workflow, while screenshots and files remain available.

Pinned Python dependency versions reduce environment drift. Base image tags and
Jenkins plugin versions can change; the build records the installed environment
and image identity. For archival reuse, retain the exact image and plugin list.
Two equal CSV files from one image on one runner do not demonstrate cross-platform
bitwise reproducibility or long-horizon predictive validity for chaotic dynamics.

The permanent evidence files and screenshots are saved in `evidence/` after a
successful hosted run. `provenance.json` identifies the exact source revision and
Actions run. Machine-readable records accompany screenshots so readers can
check the assertions without relying on a picture alone.
