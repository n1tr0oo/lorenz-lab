"""Run the existing unittest suite and export results for Jenkins."""
import argparse
import json
from pathlib import Path
import time
import unittest
import xml.etree.ElementTree as ET


class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []

    def startTest(self, test):
        super().startTest(test)
        self.started = time.monotonic()
        self.current = {"name": test.id(), "outcome": "passed"}

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.current.update(outcome="failure", detail=self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self.current.update(outcome="error", detail=self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.current.update(outcome="skipped", detail=reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err:
            kind = "failure" if issubclass(err[0], test.failureException) else "error"
            self.current.update(outcome=kind, detail=self._exc_info_to_string(err, test))

    def stopTest(self, test):
        self.current["seconds"] = time.monotonic() - self.started
        self.cases.append(self.current)
        super().stopTest(test)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("reports"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    root = ET.Element("testsuite", name="Lorenz Lab", tests=str(result.testsRun),
                      failures=str(sum(c["outcome"] == "failure" for c in result.cases)),
                      errors=str(sum(c["outcome"] == "error" for c in result.cases)),
                      skipped=str(len(result.skipped)))
    for item in result.cases:
        module, name = item["name"].rsplit(".", 1)
        case = ET.SubElement(root, "testcase", classname=module, name=name,
                             time=f'{item["seconds"]:.6f}')
        if item["outcome"] != "passed":
            ET.SubElement(case, item["outcome"]).text = item.get("detail", "")
    ET.ElementTree(root).write(args.output / "junit.xml", encoding="utf-8", xml_declaration=True)
    (args.output / "test-summary.json").write_text(json.dumps({
        "tests": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skipped": len(result.skipped),
        "passed": result.wasSuccessful(), "cases": result.cases,
    }, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
