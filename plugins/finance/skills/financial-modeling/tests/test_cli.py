import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "finance_model.py"


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def test_every_command_with_synthetic_inputs(self):
        examples = json.loads((ROOT / "assets" / "canada-examples.json").read_text())
        examples["summarize"] = {"values": [1, 2, 3]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for name in ("tax", "cpp", "resp", "withdrawals", "summarize"):
                with self.subTest(command=name):
                    path.write_text(json.dumps(examples[name]))
                    result = self.run_cli(name, path)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    output = json.loads(result.stdout)
                    self.assertEqual(output["provenance"]["command"], name)
                    self.assertEqual(len(output["provenance"]["input_sha256"]), 64)
            for name in ("project", "simulate"):
                result = self.run_cli(name, ROOT / "assets" / "fire-example.json")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("provenance", json.loads(result.stdout))
            for name in ("analyze", "backtest"):
                options = ["--initial-balance", "100000", "--rolling-years", "5",
                           "--cashflow-timing", "beginning", "--index-cashflow"] if name == "backtest" else []
                result = self.run_cli(name, ROOT / "assets" / "returns-example.csv", *options)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("provenance", json.loads(result.stdout))

    def test_invalid_json_is_not_success_shaped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for text in ('{"values":[NaN,1]}', '{"values":[1,2],"values":[3,4]}',
                         '{"values":[true,1]}', '{"values": [1,2], "typo": 1}', "null"):
                with self.subTest(text=text):
                    path.write_text(text)
                    result = self.run_cli("summarize", path)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, "")
                    self.assertIn("finance_model:", result.stderr)

    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli("project", Path(directory) / "missing.json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
