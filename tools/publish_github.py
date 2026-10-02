"""Publish this prepared repository through GitHub CLI without embedding credentials."""

import argparse
import json
from pathlib import Path
import re
import subprocess


def run(*args):
    return subprocess.run(args, text=True, check=True, capture_output=True).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Publish a new public Lorenz repository")
    parser.add_argument("--name", default="lorenz-lab")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", args.name):
        parser.error("use a simple repository name without an owner or URL")
    root = Path(__file__).resolve().parents[1]
    if Path.cwd().resolve() != root:
        parser.error("run this helper from the repository root")
    if "origin" in run("git", "remote").splitlines():
        parser.error("an origin remote already exists; refusing to create or overwrite it")
    if run("git", "status", "--porcelain"):
        parser.error("commit local changes before publication")
    run("git", "var", "GIT_AUTHOR_IDENT")
    run("gh", "auth", "status")
    # A new repository is required; an existing-name conflict fails safely.
    run("gh", "repo", "create", args.name, "--public", "--source", ".",
        "--remote", "origin", "--push", "--description",
        "Lorenz simulation, numerical tests, reproducible exports and CI/CD")
    url = run("gh", "repo", "view", "--json", "url", "--jq", ".url")
    record = {"status": "published", "repository_url": url,
              "workflow_url": url + "/blob/main/.github/workflows/ci.yml",
              "actions_url": url + "/actions", "verified_remote_run": None,
              "issue_urls": []}
    for path in sorted((root / "docs/issues").glob("*.md")):
        title = path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ")
        issue_url = run("gh", "issue", "create", "--title", title, "--body-file", str(path))
        record["issue_urls"].append(issue_url)
        (root / "docs/publication.json").write_text(json.dumps(record, indent=2) + "\n")
    run("git", "add", "docs/publication.json")
    run("git", "commit", "-m", "Record public repository and issue links")
    run("git", "push", "origin", "main")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
