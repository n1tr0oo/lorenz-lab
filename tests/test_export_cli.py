from contextlib import redirect_stdout, redirect_stderr
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from lorenz_lab.cli import main
from lorenz_lab.core import Config, simulate
from lorenz_lab.export import checksum, export_result


class ExportTests(unittest.TestCase):
    def test_manifest_checksums_and_raw_csv(self):
        result = simulate(Config(duration=1, transient=0.5))
        with tempfile.TemporaryDirectory() as folder:
            target = export_result(result, Path(folder) / "run")
            manifest = json.loads((target / "manifest.json").read_text())
            self.assertEqual(manifest["samples"], 101)
            self.assertEqual(manifest["config"]["transient"], 0.5)
            for name, expected in manifest["sha256"].items():
                self.assertEqual(checksum(target / name), expected)
            data = np.loadtxt(target / "trajectory.csv", delimiter=",", skiprows=1)
            self.assertEqual(data.shape, (101, 4))
            np.testing.assert_array_equal(data[:, 1:], result.state)
            self.assertEqual(data[0, 0], 0)  # Raw CSV retains the transient.

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "run"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_text("original")
            with self.assertRaises(FileExistsError):
                export_result(simulate(Config(duration=1, transient=0)), target)
            self.assertEqual(sentinel.read_text(), "original")

    def test_failed_export_leaves_no_partial_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "run"
            with patch("lorenz_lab.export.np.savetxt", side_effect=OSError("disk error")):
                with self.assertRaises(OSError):
                    export_result(simulate(Config(duration=1, transient=0)), target)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(folder).iterdir()), [])


class CliTests(unittest.TestCase):
    def test_defaults_are_valid_json(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(main(["--print-defaults"]), 0)
        self.assertEqual(json.loads(stream.getvalue())["sigma"], 10)

    def test_invalid_json_returns_error(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "bad.json"
            config.write_text("{broken")
            with redirect_stderr(io.StringIO()):
                status = main(["--config", str(config), "--output", str(Path(folder) / "run")])
            self.assertEqual(status, 2)
            self.assertFalse((Path(folder) / "run").exists())

    def test_unknown_config_key_returns_error(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "bad.json"
            config.write_text('{"unknown_setting": 1}')
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--config", str(config), "--output", str(Path(folder) / "run")]), 2)

    def test_cli_runs_valid_config(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "valid.json"
            config.write_text('{"duration": 1, "transient": 0}')
            target = Path(folder) / "run"
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--config", str(config), "--output", str(target)]), 0)
            self.assertTrue((target / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
