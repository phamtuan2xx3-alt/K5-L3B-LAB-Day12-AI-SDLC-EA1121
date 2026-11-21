"""Phase 3 (TICKET-03, Contract v1.2) — Độ tươi phía Lặn (DEV 1: Nguyễn Thanh Tùng).

Kiểm thử toàn diện cho hệ thống độ tươi trong giỏ lặn (hold):
- Giỏ cá thể: {id, kind, fresh}
- Hao độ tươi trong giỏ: 0.5 điểm/s = 1/120 điểm mỗi tick
- Ươn và phát sự kiện spoiled {item_id, kind, location: "hold"} khi fresh đi từ >= 30 xuống < 30
- Cấp ID và fresh = 100 khi hái hoa và bắt cá
- Bàn giao kho cá thể ở gather_end và ghi ra file kho mảng cá thể
"""

import copy
import math
import os
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.inventory import is_itemized, read_inventory, write_inventory
from chonoi.rng import Streams
from chonoi.scenario import load_scenario
from chonoi.sim.gather import GatherSim

from helpers import Workdir, write_json

STEP_GATHER = Fraction(1, 120)  # 0.5 điểm/s ở giỏ lặn = 1/120 điểm mỗi tick


def tuning_v12():
    t = copy.deepcopy(load_contract()["tuning"])
    t["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
    return t


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def make(scenario, seed=1):
    return GatherSim(tuning_v12(), scenario, Streams(seed), IdAllocator())


def step(sim, move=(0.0, 0.0), interact=False, catch=False):
    li = LiveInputs()
    li.set(move=move, interact=interact, catch=catch)
    return sim.step(li.advance())


def run_sim(sim, n):
    ev = []
    for _ in range(n):
        ev += step(sim)
    return ev


def fresh_of(sim, iid):
    return next(x["fresh"] for x in sim.snapshot()["hold"] if x["id"] == iid)


class GatherDecayAndSpoil(unittest.TestCase):
    def test_gio_lan_hao_05_moi_giay(self):
        sim = make({"random_fish": False, "hold": [item("I1", "ca_loc", 100)]})
        self.assertEqual(len(sim.snapshot()["hold"]), 1)
        run_sim(sim, 60)  # 60 ticks = 1 giây -> hao 0.5
        self.assertAlmostEqual(fresh_of(sim, "I1"), 99.5, places=9)

    def test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan(self):
        sim = make({"random_fish": False, "hold": [item("I1", "ca_linh", 30)]})
        ev = run_sim(sim, 5)
        self.assertIn(("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "hold"}), ev)
        self.assertEqual([x["id"] for x in sim.snapshot()["hold"]], ["I1"], "hàng ươn vẫn nằm trong giỏ")

    def test_sat_nguong_uon_dung_tick_va_theo_id(self):
        above = float(30 + STEP_GATHER)  # còn đúng 1 tick nữa mới xuống dưới 30
        sim = make({"random_fish": False,
                    "hold": [item("I10", "bong_sung", above), item("I2", "ca_loc", above), item("I3", "ca_loc", 31)]})
        self.assertEqual(step(sim), [], "tick 1: về đúng 30, chưa ươn (so < 30)")
        ev = step(sim)
        spoiled_evs = [e for e in ev if e[0] == "spoiled"]
        self.assertEqual([e[1]["item_id"] for e in spoiled_evs], ["I2", "I10"], "cùng tick: phát theo id, I2 trước I10")

    def test_kep_day_0(self):
        sim = make({"random_fish": False, "hold": [item("I1", "ca_loc", 0)]})
        run_sim(sim, 3)
        self.assertEqual(fresh_of(sim, "I1"), 0.0)


class GatherHarvestAndCatchFreshness(unittest.TestCase):
    def test_harvest_cap_id_va_fresh_100(self):
        # Xuất phát [2, 0], N1 [12, 0]
        sim = make({"random_fish": False, "player": {"pos": [12.0, 0.0]}})
        ev = step(sim, interact=True)
        self.assertIn(("gather", {"node_id": "N1", "kind": "bong_dien_dien"}), ev)
        snap = sim.snapshot()
        self.assertEqual(len(snap["hold"]), 1)
        it = snap["hold"][0]
        self.assertEqual(it["kind"], "bong_dien_dien")
        self.assertEqual(it["fresh"], 100.0)
        self.assertTrue(it["id"].startswith("I"))

    def test_catch_cap_id_va_fresh_100(self):
        # Bắt cá dưới nước: player [15.0, 5.0], cá F1 [15.0, 5.0]
        sim = make({"player": {"pos": [15.0, 5.0]},
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0]}],
                    "random_fish": False})
        ev = step(sim, catch=True)
        self.assertIn(("fish_caught", {"fish_id": "F1", "kind": "ca_linh"}), ev)
        snap = sim.snapshot()
        # Cá Linh yield 3 -> nhận 3 con trong giỏ
        self.assertEqual(len(snap["hold"]), 3)
        for it in snap["hold"]:
            self.assertEqual(it["kind"], "ca_linh")
            self.assertEqual(it["fresh"], 100.0)
        # Các id cá thể phải khác nhau
        ids = [it["id"] for it in snap["hold"]]
        self.assertEqual(len(set(ids)), 3)

    def test_gather_end_inventory_handoff_itemized(self):
        # Cập bến tại [2.0, 0.0] với 1 món trong giỏ
        sim = make({"random_fish": False, "player": {"pos": [2.0, 0.0]}, "hold": [item("I1", "ca_loc", 95.5)]})
        ev = step(sim, interact=True)
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "docked")
        gather_end_ev = next(e for e in ev if e[0] == "gather_end")
        inv = gather_end_ev[1]["inventory"]
        self.assertIn("items", inv)
        self.assertIsInstance(inv["items"], list)
        self.assertEqual(len(inv["items"]), 1)
        self.assertEqual(inv["items"][0]["id"], "I1")
        self.assertEqual(inv["items"][0]["kind"], "ca_loc")
        self.assertAlmostEqual(inv["items"][0]["fresh"], float(Fraction("95.5") - STEP_GATHER), places=6)


class GatherMonsterHitAndFaintItemized(unittest.TestCase):
    def test_monster_hit_drops_lifo_itemized(self):
        sim = make({
            "player": {"pos": [60.0, 24.0], "invuln_ticks": 0, "hp": 3},
            "hold": [item("I1", "ca_loc", 80), item("I2", "bong_sung", 90)],
            "monsters": [{"id": "M1", "kind": "ca_sau", "pos": [60.0, 24.0], "waypoints": [[60.0, 24.0], [64.0, 24.0]]}],
            "random_fish": False
        })
        ev = step(sim)
        hit_ev = next(e for e in ev if e[0] == "monster_hit")
        self.assertEqual(hit_ev[1]["hp"], 2)
        # Rơi floor(2/2) = 1 món LIFO (I2)
        lost = hit_ev[1]["lost"]
        self.assertEqual(len(lost), 1)
        self.assertEqual(lost[0]["id"], "I2")
        self.assertEqual(len(sim.snapshot()["hold"]), 1)
        self.assertEqual(sim.snapshot()["hold"][0]["id"], "I1")


if __name__ == "__main__":
    unittest.main()
