"""Command-line adapter; failures produce a concise error and nonzero status."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from .core import Config, SimulationError, simulate
from .export import export_result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulate and export the Lorenz system")
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    parser.add_argument("--output", type=Path, default=Path("results/run"))
    parser.add_argument("--print-defaults", action="store_true")
    args = parser.parse_args(argv)
    if args.print_defaults:
        print(json.dumps(asdict(Config()), indent=2))
        return 0
    try:
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        data = json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
        if not isinstance(data, dict):
            raise ValueError("configuration must be a JSON object")
        result = simulate(Config(**data))
        target = export_result(result, args.output)
    except (ValueError, TypeError, OSError, SimulationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Saved {len(result.time)} samples and provenance to {target}")
    return 0
