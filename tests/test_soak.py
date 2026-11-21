"""TICKET-04 mục 2 — soak headless nhiều Ngày (DEV 3).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_soak -v
"""

import json
import shlex
import subprocess
import sys
import unittest

from chonoi.soak import run_soak

from helpers import ROOT, Workdir, read_jsonl  # noqa: F401  (ROOT dùng cho subprocess)

GAMEPLAY = ("days", "days_completed", "crashes", "results")


class Soak(unittest.TestCase):
    def test_10_ngay_khong_crash_va_lap_ke_hoach(self):
        r = run_soak(7, 10)
        self.assertEqual((r["days_completed"], r["crashes"]), (10, 0))
        self.assertEqual([x["day"] for x in r["results"]], list(range(1, 11)))
        for x in r["results"]:
            self.assertEqual(set(x), {"day", "earned", "reputation", "score"})
            self.assertEqual(x["score"], x["earned"] + 100 * int(x["reputation"]))
        earned = [x["earned"] for x in r["results"]]
        self.assertEqual(earned, sorted(earned), "earned cộng dồn xuyên Ngày, không reset")

    def test_tat_dinh_bo_qua_duration(self):
        a, b = run_soak(7, 3), run_soak(7, 3)
        self.assertEqual({k: a[k] for k in GAMEPLAY}, {k: b[k] for k in GAMEPLAY})

    def test_ke_hoach_ngay_6_10_lap_d1_d5(self):
        from chonoi.contract import load_contract
        from chonoi.ids import IdAllocator
        from chonoi.rng import Streams
        from chonoi.sim.day import DaySim
        day = DaySim(load_contract()["tuning"], {}, Streams(1), IdAllocator(), total_days=10)
        for n in range(1, 11):
            self.assertEqual(day._get_plan(n)["day"], (n - 1) % 5 + 1)

    def test_soak_cmd_trong_contract_ghi_dung_schema(self):
        with open(f"{ROOT}/game.contract.json", encoding="utf-8") as f:
            cmd = shlex.split(json.load(f)["soak_cmd"])
        if cmd[0] == "python3":
            cmd[0] = sys.executable
        with Workdir() as w:
            out = w.path("soak.json")
            p = subprocess.run([*cmd, "--seed", "7", "--days", "2", "--out", out], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(set(data), {"days", "days_completed", "crashes", "results", "duration_s"})
            self.assertEqual((data["days"], data["days_completed"], data["crashes"]), (2, 2, 0))
            bad = subprocess.run([*cmd, "--seed", "7", "--out", out], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2, "thiếu --days -> mã 2")


if __name__ == "__main__":
    unittest.main()
