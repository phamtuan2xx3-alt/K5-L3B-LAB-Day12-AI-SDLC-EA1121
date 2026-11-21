"""Phase 3 (TICKET-03, Contract v1.2) — độ tươi phía Quán (DEV 3).

Dựng tuning v1.2 trong test (thêm `freshness`), nên chạy được trước khi game.contract.json đổi sang 1.2.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_freshness -v
"""

import copy
import json
import math
import os
import unittest
from fractions import Fraction

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.inventory import read_inventory, write_inventory
from chonoi.rng import Streams
from chonoi.scenario import _validate_quan
from chonoi.sim.quan import QuanSim

from helpers import Workdir, write_json

STEP = Fraction(1, 240)  # 0.25 điểm/s ở quán = 1/240 điểm mỗi tick


def tuning_v12():
    t = copy.deepcopy(load_contract()["tuning"])
    t["freshness"] = {"initial": 100, "gather_decay_per_s": 0.5, "quan_decay_per_s": 0.25, "spoiled_below": 30}
    return t


def item(iid, kind, fresh):
    return {"id": iid, "kind": kind, "fresh": fresh}


def make(scenario, seed=1):
    return QuanSim(tuning_v12(), scenario, Streams(seed), IdAllocator())


def step(sim, interact=False):
    li = LiveInputs()
    li.set(interact=interact)
    return sim.step(li.advance())


def run(sim, n):
    ev = []
    for _ in range(n):
        ev += step(sim)
    return ev


def fresh_of(sim, iid):
    return next(x["fresh"] for x in sim.snapshot()["stock"] if x["id"] == iid)


class DecayAndSpoil(unittest.TestCase):
    def test_kho_quan_hao_025_moi_giay_ke_ca_hang_dang_giu(self):
        sim = make({"random_customers": False, "stock": [item("I1", "ca_loc", 100)],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]})
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I1"])
        run(sim, 60)
        self.assertAlmostEqual(fresh_of(sim, "I1"), 99.75, places=9)

    def test_dung_30_uon_o_buoc_dau_phat_spoiled_mot_lan(self):
        sim = make({"random_customers": False, "stock": [item("I1", "ca_linh", 30)]})
        ev = run(sim, 5)
        self.assertEqual(ev, [("spoiled", {"item_id": "I1", "kind": "ca_linh", "location": "stock"})])
        self.assertEqual([x["id"] for x in sim.snapshot()["stock"]], ["I1"], "hàng ươn vẫn nằm trong kho")

    def test_sat_nguong_uon_dung_tick_va_theo_id(self):
        above = float(30 + STEP)  # còn đúng 1 tick nữa mới xuống dưới 30
        sim = make({"random_customers": False,
                    "stock": [item("I10", "bong_sung", above), item("I2", "ca_loc", above), item("I3", "ca_loc", 31)]})
        self.assertEqual(step(sim), [], "tick 1: về đúng 30, chưa ươn (so < 30)")
        ev = step(sim)
        self.assertEqual([e[1]["item_id"] for e in ev], ["I2", "I10"], "cùng tick: phát theo id, I2 trước I10")

    def test_kep_day_0(self):
        sim = make({"random_customers": False, "stock": [item("I1", "ca_loc", 0)]})
        run(sim, 3)
        self.assertEqual(fresh_of(sim, "I1"), 0.0)


class HoldByIdAndRehold(unittest.TestCase):
    def test_khach_moi_giu_ca_the_tuoi_nhat_hoa_theo_id(self):
        sim = make({"stock": [item("I1", "bong_sung", 60), item("I2", "bong_sung", 90),
                              item("I3", "bong_sung", 90), item("I4", "bong_sung", 70)]})
        run(sim, 120)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["dish_id"], c["reserved"]), ("goi_bong_sung", ["I2", "I3"]))

    def test_hang_dang_giu_vua_uon_thi_nha_va_giu_lai(self):
        sim = make({"random_customers": False,
                    "stock": [item("I1", "ca_loc", float(30 + STEP)), item("I2", "ca_loc", 50)],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]})
        run(sim, 2)
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"]), ("reserved", ["I2"]))

    def test_giu_lai_khong_du_thi_unfulfillable_khach_van_cho(self):
        sim = make({"random_customers": False, "stock": [item("I1", "ca_loc", 30)],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]})
        ev = step(sim)
        self.assertEqual([e[0] for e in ev], ["spoiled"])
        c = sim.snapshot()["customers"][0]
        self.assertEqual((c["order_status"], c["reserved"], c["state"]), ("unfulfillable", [], "waiting"))

    def test_hang_uon_khong_dung_cho_khach_moi(self):
        sim = make({"stock": [item("I1", "ca_loc", 29)]})
        self.assertIn(("no_dish", {}), run(sim, 120))


class FreshPrice(unittest.TestCase):
    def cook(self, stock, dish, reserved):
        sim = make({"player": {"pos": [2, 8]}, "random_customers": False, "stock": stock,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": dish, "reserved": reserved}]})
        ev = step(sim, interact=True)
        return sim, [e for e in ev if e[0] == "cook_started"][0][1]

    def test_gia_chot_theo_trung_binh_fresh_sau_lan_hao_cua_buoc(self):
        sim, ev = self.cook([item("I1", "ca_loc", 50)], "ca_loc_nuong_trui", ["I1"])
        expected = math.floor(60 * (Fraction(50) - STEP) / 100)  # 29.9975 -> 29: hao trước, nấu sau
        self.assertEqual((ev["base_price"], expected), (29, 29))
        self.assertEqual(sim.snapshot()["stoves"][0]["dish"]["base_price"], 29)
        self.assertEqual(sim.snapshot()["stock"], [], "tiêu đúng id đang giữ")

    def test_items_la_ca_the_sap_theo_kind_roi_id(self):
        stock = [item("I9", "ca_linh", 90), item("I2", "ca_linh", 90), item("I5", "ca_linh", 90),
                 item("I7", "bong_dien_dien", 80), item("I8", "ca_linh", 40)]
        _, ev = self.cook(stock, "lau_ca_linh_dien_dien", ["I2", "I5", "I7", "I9"])
        self.assertEqual([(x["id"], x["kind"]) for x in ev["items"]],
                         [("I7", "bong_dien_dien"), ("I2", "ca_linh"), ("I5", "ca_linh"), ("I9", "ca_linh")])
        mean = (3 * (Fraction(90) - STEP) + Fraction(80) - STEP) / 4
        self.assertEqual(ev["base_price"], math.floor(120 * mean / 100))

    def test_boa_tinh_tren_gia_da_chot(self):
        sc = {"player": {"pos": [9, 2]}, "random_customers": False, "stock": [],
              "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 33},
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "order_status": "assigned"}]}
        ev = step(make(sc), interact=True)
        self.assertEqual(ev[0][1]["tip"], 6, "floor(33 x 0.2)")


class FixtureV12(unittest.TestCase):
    def bad(self, sc):
        with self.assertRaises(BadInput):
            make(sc)

    def test_bo_reserved_thi_cap_tuoi_nhat_theo_order_tick(self):
        sim = make({"random_customers": False,
                    "stock": [item("I1", "bong_sung", 50), item("I2", "bong_sung", 99), item("I3", "bong_sung", 80)],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung"}]})
        self.assertEqual(sim.snapshot()["customers"][0]["reserved"], ["I2", "I3"])

    def test_giu_ca_the_uon(self):
        self.bad({"stock": [item("I1", "ca_loc", 20)],
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]})

    def test_giu_ca_the_khong_co(self):
        self.bad({"stock": [], "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                              "reserved": ["I9"]}]})

    def test_hai_don_giu_chung_id(self):
        self.bad({"stock": [item("I1", "ca_loc", 90)], "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]},
            {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "reserved": ["I1"]}]})

    def test_giu_khac_cong_thuc(self):
        self.bad({"stock": [item("I1", "ca_loc", 90), item("I2", "ca_loc", 90)],
                  "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                 "reserved": ["I1", "I2"]}]})

    def test_scenario_stock_dem_bi_tu_choi_o_v12(self):
        with self.assertRaises(BadInput):
            _validate_quan({"stock": {"ca_loc": 1}}, tuning_v12())
        for bad in ([item("I1", "ca_loc", 101)], [item("I1", "ca_loc", 5), item("I1", "ca_loc", 6)],
                    [item("I1", "ca_heo", 5)], [{"id": "I1", "kind": "ca_loc"}]):
            with self.assertRaises(BadInput):
                _validate_quan({"stock": bad}, tuning_v12())


class InventoryFileV12(unittest.TestCase):
    def test_ghi_doc_lai_chinh_xac_va_quan_nhan_nguyen_ven(self):
        with Workdir() as w:
            p = w.path("catch.json")
            near = 30 + STEP * 3
            write_inventory(p, [{"id": "I2", "kind": "ca_loc", "fresh": near}, item("I1", "ca_linh", 100)])
            with open(p, encoding="utf-8") as f:
                raw = json.load(f)
            self.assertEqual([x["id"] for x in raw["items"]], ["I1", "I2"], "xuất theo id")
            kinds = ("bong_dien_dien", "bong_sung", "ca_keo", "ca_linh", "ca_loc", "keo_neo")
            back = read_inventory(p, kinds, itemized=True)
            self.assertEqual(Fraction(str(back[1]["fresh"])) if not isinstance(back[1]["fresh"], Fraction)
                             else back[1]["fresh"], Fraction(str(float(near))))
            sim = QuanSim(tuning_v12(), {}, Streams(1), IdAllocator(), inventory=back)
            self.assertEqual(sim.snapshot()["stock"], raw["items"], "snapshot tick 0 khớp file")
            run(sim, 2)
            self.assertNotIn("spoiled", [e[0] for e in run(sim, 1)], "còn trên 30 sau 3 tick: chưa ươn")

    def test_file_kho_dem_tra_ma_2_o_v12(self):
        with Workdir() as w:
            p = write_json(w.path("old.json"), {"items": {"ca_loc": 1}})
            with self.assertRaises(BadInput):
                read_inventory(p, ("ca_loc",), itemized=True)
            self.assertEqual(read_inventory(p, ("ca_loc",)), {"ca_loc": 1}, "v1.1 vẫn đọc kho đếm")


if __name__ == "__main__":
    unittest.main()
