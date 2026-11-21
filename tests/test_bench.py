"""TICKET-04 mục 1 — Benchmark hiệu năng cảnh lặn (DEV 5).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_bench -v
"""

import json
import os
import shlex
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chonoi.bench import run_benchmark
from helpers import ROOT, Workdir

BENCH_KEYS = {"avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"}


class BenchmarkTest(unittest.TestCase):
    def test_run_benchmark_structure_and_thresholds(self):
        report = run_benchmark(42, 1)
        self.assertEqual(set(report), BENCH_KEYS)
        self.assertGreaterEqual(report["avg_fps"], 60.0)
        self.assertGreaterEqual(report["p1_low_fps"], 30.0)
        self.assertLessEqual(report["load_ms"], 10000)
        self.assertGreater(report["frames"], 50)
        self.assertGreater(report["measured_s"], 0.9)

    def test_bench_cmd_in_contract_and_cli(self):
        with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
            c = json.load(f)
            self.assertIn("bench_cmd", c)
            cmd = shlex.split(c["bench_cmd"])

        if cmd[0] == "python3":
            cmd[0] = sys.executable

        with Workdir() as w:
            out_file = w.path("bench.json")
            # Run 1 second test
            p = subprocess.run([*cmd, "--seed", "42", "--duration", "1", "--out", out_file],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)

            with open(out_file, encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(set(data), BENCH_KEYS)
            self.assertGreaterEqual(data["avg_fps"], 60.0)
            self.assertGreaterEqual(data["p1_low_fps"], 30.0)
            self.assertLessEqual(data["load_ms"], 10000)

            # Test missing arguments return exit code 2
            bad = subprocess.run([*cmd, "--seed", "42", "--out", out_file],
                                 cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2, "thiếu --duration -> mã 2")

            bad_dur = subprocess.run([*cmd, "--seed", "42", "--duration", "0", "--out", out_file],
                                     cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(bad_dur.returncode, 2, "duration < 1 -> mã 2")


if __name__ == "__main__":
    unittest.main()
