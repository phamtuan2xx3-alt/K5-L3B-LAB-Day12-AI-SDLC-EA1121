"""Lát 3 (DEV 3) — vòng đời khách quán theo PRD-0 mục D/E/F.

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_customers -v
"""

import unittest

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import LiveInputs
from chonoi.runner import Session
from chonoi.sim import customers as cust

from helpers import Workdir, read_jsonl, run_headless, write_json

TUNING = load_contract()["tuning"]
FIRST = TUNING["quan"]["first_customer_tick"]                       # 120
INTERVAL = int(round(TUNING["quan"]["customer_interval_s"] * 60))   # 900
PATIENCE = int(round(TUNING["quan"]["patience_s"] * 60))            # 3600


def run_until(sess, tick):
    """Chạy không điều khiển tới khi sess.tick == tick; trả mọi event theo thứ tự."""
    li, rows = LiveInputs(), []
    while sess.tick < tick and not sess.done:
        rows += sess.step(li.advance())
    return rows


def names(rows):
    return [(r["tick"], r["name"]) for r in rows]


class Arrivals(unittest.TestCase):
    def test_khach_dau_tien_dung_first_customer_tick(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 1}}, 1)
        rows = run_until(s, FIRST)
        self.assertEqual(names(rows), [(FIRST, "customer_arrived")])
        self.assertEqual(rows[0]["data"], {"order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"})
        c = s.snapshot()["customers"][0]
        self.assertEqual((c["order_tick"], c["state"], c["order_status"]), (FIRST, "waiting", "reserved"))
        self.assertEqual(c["patience_ticks_left"], PATIENCE, "kiên nhẫn đầy, bắt đầu giảm từ bước sau")
        self.assertEqual(c["reserved"], {"ca_loc": 1})
        self.assertEqual(s.snapshot()["tables"][0]["customer_id"], "C1")
        self.assertEqual(s.snapshot()["stock"], {"ca_loc": 1}, "stock là tồn vật lý, gồm cả phần giữ")

    def test_kho_rong_phat_no_dish(self):
        s = Session("quan", TUNING, {}, 1)
        rows = run_until(s, FIRST)
        self.assertEqual(names(rows), [(FIRST, "no_dish")])
        self.assertEqual(rows[0]["data"], {})
        self.assertEqual(s.snapshot()["customers"], [])

    def test_het_ban_bo_luot_khong_event(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 2}}, 1)
        rows = run_until(s, FIRST + INTERVAL)
        self.assertEqual(names(rows), [(FIRST, "customer_arrived")], "T1 đang có khách: lượt 1020 bị bỏ")

    def test_random_customers_false_tat_khach_tu_sinh(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 1}, "random_customers": False}, 1)
        self.assertEqual(run_until(s, FIRST + INTERVAL), [])

    def test_chon_mon_tat_dinh_theo_seed(self):
        stock = {"ca_loc": 1, "bong_sung": 2, "ca_linh": 3, "bong_dien_dien": 1}
        picks = []
        for _ in range(2):
            s = Session("quan", TUNING, {"stock": stock}, 7)
            picks.append(run_until(s, FIRST)[0]["data"]["dish_id"])
        self.assertEqual(picks[0], picks[1])
        self.assertIn(picks[0], TUNING["menu"])

    def test_kho_kha_dung_tru_phan_giu(self):
        sc = {"stock": {"ca_loc": 1, "bong_sung": 2}, "random_customers": False,
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}
        sim = Session("quan", TUNING, sc, 1).sim
        self.assertEqual(sim.customers[0]["reserved"], {"ca_loc": 1}, "thiếu reserved -> cấp theo công thức")
        self.assertEqual(cust.cookable_dishes(sim), ["goi_bong_sung"])


class PatienceAndLeaving(unittest.TestCase):
    def test_het_kien_nhan_roi_tru_uy_tin_va_nha_giu_cho(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 1}}, 1)
        leave_tick = FIRST + PATIENCE
        rows = run_until(s, leave_tick)
        self.assertEqual(names(rows)[-1], (leave_tick, "customer_arrived"),
                         "3720 trùng lịch khách: rời trước (bước 4) rồi khách mới vào (bước 5)")
        left = [r for r in rows if r["name"] == "customer_left"]
        self.assertEqual(len(left), 1)
        self.assertEqual(left[0]["tick"], leave_tick)
        self.assertEqual(left[0]["data"], {"order_id": "C1", "table_id": "T1", "reason": "patience",
                                           "reputation": 2.5})
        snap = s.snapshot()
        self.assertEqual(snap["reputation"], 2.5)
        self.assertEqual([c["id"] for c in snap["customers"]], ["C2"], "giữ chỗ của C1 đã nhả cho C2")

    def test_kien_nhan_giam_tu_buoc_sau(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 1}}, 1)
        run_until(s, FIRST + 10)
        self.assertEqual(s.snapshot()["customers"][0]["patience_ticks_left"], PATIENCE - 10)

    def test_dong_ca_khach_cho_roi_closing_khong_tru_uy_tin(self):
        s = Session("quan", TUNING, {"stock": {"ca_loc": 1}, "time_left_ticks": 200}, 1)
        rows = run_until(s, 10_000)
        self.assertEqual(names(rows), [(FIRST, "customer_arrived"), (200, "customer_left"), (200, "quan_end")])
        self.assertEqual(rows[1]["data"]["reason"], "closing")
        self.assertEqual(rows[1]["data"]["reputation"], 3.0)
        self.assertEqual(s.snapshot()["customers"], [])

    def test_roi_quan_bo_mon_cua_don_tren_tay(self):
        sc = {"stock": {}, "random_customers": False,
              "hand": {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
              "customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                             "order_status": "assigned", "patience_ticks_left": 1}]}
        s = Session("quan", TUNING, sc, 1)
        rows = run_until(s, 1)
        self.assertEqual(names(rows), [(1, "customer_left")])
        self.assertIsNone(s.snapshot()["hand"])

    def test_an_xong_tra_tien_va_id_moi_noi_tiep(self):
        sc = {"stock": {"ca_loc": 1},
              "customers": [{"id": "C5", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                             "order_status": "served", "eat_ticks_left": 1, "base_price": 40, "tip": 8}]}
        s = Session("quan", TUNING, sc, 1)
        rows = run_until(s, FIRST)
        self.assertEqual(names(rows), [(1, "paid"), (FIRST, "customer_arrived")])
        self.assertEqual(rows[0]["data"], {"order_id": "C5", "table_id": "T1", "base_price": 40, "tip": 8,
                                           "amount": 48, "reason": "finished_eating"})
        self.assertEqual(rows[1]["data"]["order_id"], "C6")
        snap = s.snapshot()
        self.assertEqual((snap["money"], snap["earned"], snap["reputation"]), (48, 48, 3.2))


class FixtureValidation(unittest.TestCase):
    def bad(self, sc):
        with self.assertRaises(BadInput):
            Session("quan", TUNING, sc, 1)

    def test_giu_qua_ton(self):
        self.bad({"stock": {}, "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]})

    def test_giu_khac_cong_thuc(self):
        self.bad({"stock": {"ca_loc": 2}, "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "reserved": {"ca_loc": 2}}]})

    def test_truong_la(self):
        self.bad({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "mood": "vui"}]})

    def test_eating_thieu_gia(self):
        self.bad({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating",
                                 "order_status": "served", "eat_ticks_left": 5}]})

    def test_assigned_khong_co_mon(self):
        self.bad({"customers": [{"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                 "order_status": "assigned"}]})

    def test_kien_nhan_vuot_tran(self):
        self.bad({"stock": {"bong_sung": 2}, "customers": [
            {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "patience_ticks_left": PATIENCE + 1}]})


class Headless(unittest.TestCase):
    def test_hop_den_khach_den_va_mau_thuan_ma_2(self):
        with Workdir() as w:
            sc = write_json(w.path("sc.json"), {"quan": {"stock": {"ca_loc": 1}}})
            out = w.path("q.jsonl")
            code, err = run_headless("--mode", "quan", "--seed", "1", "--scenario", sc, "--ticks", str(FIRST),
                                     "--out", out)
            self.assertEqual(code, 0, err)
            ev = [r for r in read_jsonl(out) if r["type"] == "event"]
            self.assertEqual([(e["tick"], e["name"]) for e in ev], [(FIRST, "customer_arrived")])
            bad = write_json(w.path("bad.json"), {"quan": {"customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}]}})
            self.assertEqual(run_headless("--mode", "quan", "--seed", "1", "--scenario", bad, "--ticks", "0",
                                          "--out", w.path("b.jsonl"))[0], 2)


if __name__ == "__main__":
    unittest.main()
