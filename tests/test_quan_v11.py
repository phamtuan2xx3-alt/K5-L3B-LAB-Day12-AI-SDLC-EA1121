"""Lát 3 Quán v1.1 (DEV 3) — TICKET-02 mục 1.3 + 2: 2 bếp, 4 bàn, 6 món, kế hoạch Ngày.

Dùng bộ số chuẩn v1.1 dựng trong test (không phụ thuộc game.contract.json đang ở bản nào), nên chạy
được trước và sau khi nhóm đổi contract sang 1.1.
Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_v11 -v
"""

import copy
import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.inventory import kinds_for, validate_items
from chonoi.rng import Streams
from chonoi.sim import customers as cust
from chonoi.sim.quan import QuanSim
from helpers import counts_tuning

MENU_V11 = {
    "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
    "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
    "lau_ca_linh_dien_dien": {"recipe": {"ca_linh": 3, "bong_dien_dien": 1}, "cook_s": 10, "price": 120},
    "canh_chua_ca_loc": {"recipe": {"ca_loc": 1, "bong_dien_dien": 1}, "cook_s": 8, "price": 90},
    "ca_keo_nuong": {"recipe": {"ca_keo": 2}, "cook_s": 6, "price": 70},
    "lau_mam": {"recipe": {"ca_linh": 2, "ca_keo": 1, "keo_neo": 1, "bong_dien_dien": 1}, "cook_s": 12,
                "price": 200},
}
D1_DISHES = {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3}
FULL_STOCK = {"ca_loc": 9, "ca_linh": 9, "bong_dien_dien": 9, "bong_sung": 9, "ca_keo": 9, "keo_neo": 9}


def tuning_v11():
    t = counts_tuning()  # bố cục v1.1 với kho đếm; kho cá thể v1.2 xem test_quan_freshness
    t["quan"]["stoves"] = [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}]
    t["quan"]["tables"] = [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]},
                           {"id": "T3", "pos": [9, 6]}, {"id": "T4", "pos": [13, 6]}]
    t["menu"] = copy.deepcopy(MENU_V11)
    return t


def make(scenario, seed=1, allowed=None):
    return QuanSim(tuning_v11(), scenario, Streams(seed), IdAllocator(), allowed_dishes=allowed)


def step(sim, interact=False):
    li = LiveInputs()
    li.set(interact=interact)
    return sim.step(li.advance())


def run(sim, n):
    ev = []
    for _ in range(n):
        ev += step(sim)
    return ev


class LayoutV11(unittest.TestCase):
    def test_bon_ban_nhan_khach_theo_id_nho_nhat(self):
        sim = make({"stock": FULL_STOCK})
        ev = [e for e in run(sim, 120 + 3 * 900) if e[0] == "customer_arrived"]
        self.assertEqual([e[1]["table_id"] for e in ev], ["T1", "T2", "T3", "T4"])
        self.assertEqual([e[1]["order_id"] for e in ev], ["C1", "C2", "C3", "C4"])
        ev5 = [e for e in run(sim, 900) if e[0] in ("customer_left", "customer_arrived")]
        self.assertEqual([(e[0], e[1]["order_id"], e[1]["table_id"]) for e in ev5],
                         [("customer_left", "C1", "T1"), ("customer_arrived", "C5", "T1")],
                         "3720: C1 hết kiên nhẫn (120 + 3600) nhả T1, C5 vào T1 cùng tick")

    def test_hai_bep_nau_song_song_hai_don(self):
        sc = {"player": {"pos": [3.5, 8]}, "random_customers": False, "stock": FULL_STOCK,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "order_tick": 5},
                            {"id": "C2", "table_id": "T2", "dish_id": "ca_keo_nuong", "order_tick": 3}]}
        sim = make(sc)
        e1 = step(sim, interact=True)
        self.assertEqual((e1[0][0], e1[0][1]["stove_id"], e1[0][1]["order_id"]), ("cook_started", "B1", "C2"),
                         "cách đều B1/B2: bếp id nhỏ trước; đơn cũ nhất theo order_tick")
        self.assertEqual(e1[0][1]["items"], ["ca_keo", "ca_keo"])
        self.assertEqual(step(sim, interact=True), [],
                         "vẫn chọn B1 (cùng khoảng cách, id nhỏ) nhưng B1 đang nấu: bỏ lượt, không thử B2")
        sim.pos = [5.0, 8.0]
        e2 = step(sim, interact=True)
        self.assertEqual((e2[0][1]["stove_id"], e2[0][1]["order_id"]), ("B2", "C1"))
        self.assertEqual([s["state"] for s in sim.stoves], ["cooking", "cooking"])

    def test_ban_gan_hon_thang_bep(self):
        sc = {"player": {"pos": [9, 3]}, "random_customers": False,
              "hand": {"order_id": "C1", "dish_id": "lau_mam", "base_price": 200},
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_mam", "order_status": "assigned"}]}
        ev = step(make(sc), interact=True)
        self.assertEqual(ev[0][0], "served")
        self.assertEqual(ev[0][1]["tip"], 40, "floor(200 x 0.2)")


class DayPlanFilter(unittest.TestCase):
    def test_loc_theo_ke_hoach_truoc_khi_xet_kho(self):
        sim = make({"stock": FULL_STOCK}, allowed=D1_DISHES)
        self.assertEqual(cust.menu_pool(sim), ["ca_loc_nuong_trui", "goi_bong_sung"])
        self.assertEqual(cust.cookable_dishes(sim), ["ca_loc_nuong_trui", "goi_bong_sung"])

    def test_khach_chi_goi_mon_trong_ke_hoach(self):
        picks = set()
        for seed in range(12):
            sim = make({"stock": FULL_STOCK}, seed=seed, allowed=D1_DISHES)
            picks |= {e[1]["dish_id"] for e in run(sim, 120) if e[0] == "customer_arrived"}
        self.assertLessEqual(picks, set(D1_DISHES))
        self.assertEqual(picks, set(D1_DISHES), "chọn đều theo seed: 12 seed phải gặp cả hai món")

    def test_kho_thieu_mon_ke_hoach_thi_no_dish_du_con_mon_khac(self):
        sim = make({"stock": {"ca_keo": 2}}, allowed=D1_DISHES)
        self.assertEqual([e for e in run(sim, 120) if e[0] in ("no_dish", "customer_arrived")], [("no_dish", {})])

    def test_quan_rieng_dung_ca_6_mon(self):
        sim = make({"stock": {"ca_keo": 2}})
        ev = [e for e in run(sim, 120) if e[0] == "customer_arrived"]
        self.assertEqual(ev[0][1]["dish_id"], "ca_keo_nuong")

    def test_goi_tiep_mon_du_nguyen_lieu_khi_da_ban_du_suat(self):
        sim = make({"stock": {"ca_loc": 9}}, allowed={"ca_loc_nuong_trui": 1})
        ev = [e for e in run(sim, 120 + 900) if e[0] == "customer_arrived"]
        self.assertEqual(len(ev), 2, "số suất chỉ để tính mục tiêu thu gom, không chặn khách")


class IngredientsV11(unittest.TestCase):
    def test_kho_v11_nhan_ca_keo_keo_neo(self):
        self.assertEqual(kinds_for(tuning_v11()),
                         ("bong_dien_dien", "bong_sung", "ca_keo", "ca_linh", "ca_loc", "keo_neo"))
        self.assertEqual(validate_items({"ca_keo": 2, "keo_neo": 1}, kinds_for(tuning_v11())),
                         {"ca_keo": 2, "keo_neo": 1})

    def test_contract_p1_van_tu_choi_ca_keo(self):
        p1 = {"menu": {k: MENU_V11[k] for k in ("ca_loc_nuong_trui", "goi_bong_sung", "lau_ca_linh_dien_dien")}}
        with self.assertRaises(BadInput):
            validate_items({"ca_keo": 1}, kinds_for(p1))


if __name__ == "__main__":
    unittest.main()
