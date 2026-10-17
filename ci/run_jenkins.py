"""Launch a real, disposable Jenkins controller on a Docker-capable CI host."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8080"
DEST = Path("docs/assignment5/evidence")
DEST.mkdir(parents=True, exist_ok=True)


def get(path, as_json=True):
    with urllib.request.urlopen(BASE + path, timeout=15) as response:
        data = response.read()
    return json.loads(data) if as_json else data


def main():
    revision = os.environ.get("LORENZ_REF", os.environ.get("GITHUB_SHA", "assignment-5-devops"))
    subprocess.run(["docker", "build", "-f", "ci/jenkins/Dockerfile", "-t", "lorenz-jenkins", "."], check=True)
    subprocess.run(["docker", "run", "-d", "--name", "lorenz-jenkins", "--network", "host",
                    "--user", "root", "-v", "/var/run/docker.sock:/var/run/docker.sock",
                    "-v", "lorenz-jenkins-home:/var/jenkins_home",
                    "-e", "JAVA_OPTS=-Djenkins.install.runSetupWizard=false",
                    "-e", "LORENZ_REF=" + revision,
                    "lorenz-jenkins", "--httpListenAddress=127.0.0.1", "--httpPort=8080"], check=True)
    summary = None
    for attempt in range(360):
        try:
            summary = get("/job/lorenz-lab/lastBuild/api/json")
            if not summary.get("building", True) and summary.get("result"):
                break
        except (OSError, ValueError, urllib.error.HTTPError):
            pass
        if attempt % 12 == 0:
            print(f"Waiting for Jenkins build, elapsed approximately {attempt * 5} seconds", flush=True)
        time.sleep(5)
    else:
        subprocess.run(["docker", "logs", "--tail", "100", "lorenz-jenkins"])
        raise SystemExit("Jenkins did not finish within 30 minutes")
    number = summary["number"]
    prefix = f"/job/lorenz-lab/{number}"
    console = get(prefix + "/consoleText", as_json=False)
    (DEST / "jenkins-console.txt").write_bytes(console)
    print(console.decode(errors="replace"), flush=True)
    (DEST / "jenkins-build.json").write_text(json.dumps(summary, indent=2) + "\n")
    for endpoint, name in [("/wfapi/describe", "jenkins-stages.json"),
                           ("/testReport/api/json", "jenkins-tests.json")]:
        try:
            (DEST / name).write_text(json.dumps(get(prefix + endpoint), indent=2) + "\n")
        except OSError:
            pass
    plugins = get("/pluginManager/api/json?tree=plugins[shortName,version]")
    (DEST / "jenkins-plugins.json").write_text(json.dumps(plugins, indent=2) + "\n")
    for item in summary.get("artifacts", []):
        relative = item["relativePath"]
        if relative.startswith(("reports/", "results/run-1/")):
            target = DEST / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(get(prefix + "/artifact/" + relative, as_json=False))
    provenance = {"github_run_url": os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" +
                  os.environ.get("GITHUB_REPOSITORY", "n1tr0oo/lorenz-lab") + "/actions/runs/" +
                  os.environ.get("GITHUB_RUN_ID", "local"),
                  "source_commit": revision, "jenkins_build": number,
                  "jenkins_result": summary["result"],
                  "jenkins_scope": "Disposable real Jenkins controller hosted on the CI runner",
                  "controller_url": BASE, "test_deployment_url": "http://127.0.0.1:8090/"}
    (DEST / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    if summary["result"] != "SUCCESS":
        raise SystemExit("Jenkins build failed: " + summary["result"])


if __name__ == "__main__":
    main()
