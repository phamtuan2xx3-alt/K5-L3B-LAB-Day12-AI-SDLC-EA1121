"""Unit tests cho phần Bếp nấu, Bưng bê & Kinh tế quán (`chonoi/sim/quan.py`).
Phụ trách bởi DEV 5: Chu Văn Nhật (moyymochi11).
"""

import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session


class TestQuanKitchenServing(unittest.TestCase):
    def setUp(self):
        self.tuning = load_contract()["tuning"]

    def test_stove_cook_ready_pick_serve_and_pay(self):
        """Kiểm tra toàn bộ chu trình: Bếp nấu -> Chín -> Bốc món -> Phục vụ -> Khách ăn -> Trả tiền + Boa."""
        scenario = {
            "player": {"pos": [2, 8]},  # Đứng sát bếp B1 [2, 8]
            "stock": {"ca_loc": 2},
            "customers": [
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish": "ca_loc_nuong_trui",
                    "state": "waiting",
                    "patience_ticks": 3600,
                }
            ],
            "stoves": [{"id": "B1", "pos": [2, 8]}],
            "tables": [{"id": "T1", "pos": [9, 2]}],
            "time_left_ticks": 10000,
        }
        s = Session("quan", self.tuning, scenario, seed=1)
        li = LiveInputs()

        # 1. Bấm interact tại bếp B1 -> Bắt đầu nấu
        li.set(interact=True)
        events = s.step(li.advance())
        li.set(interact=False)

        ev_names = [e["name"] for e in events]
        self.assertIn("cook_started", ev_names)
        snap = s.snapshot()
        self.assertEqual(snap["stock"].get("ca_loc", 0), 1)  # Đã trừ 1 cá lóc
        stove = next(st for st in snap["stoves"] if st["id"] == "B1")
        self.assertEqual(stove["state"], "cooking")
        self.assertEqual(stove["dish"], "ca_loc_nuong_trui")

        # 2. Đợi 360 ticks (6 giây) -> Bếp chín
        ready_found = False
        for _ in range(360):
            evs = s.step(li.advance())
            for e in evs:
                if e["name"] == "dish_ready":
                    ready_found = True
                    self.assertEqual(e["data"]["dish"], "ca_loc_nuong_trui")
        self.assertTrue(ready_found)
        snap = s.snapshot()
        stove = next(st for st in snap["stoves"] if st["id"] == "B1")
        self.assertEqual(stove["state"], "ready")

        # 3. Bấm interact tại bếp B1 -> Bốc món lên tay
        li.set(interact=True)
        events = s.step(li.advance())
        li.set(interact=False)
        self.assertIn("dish_picked", [e["name"] for e in events])
        snap = s.snapshot()
        self.assertEqual(snap["hand"], "ca_loc_nuong_trui")
        stove = next(st for st in snap["stoves"] if st["id"] == "B1")
        self.assertEqual(stove["state"], "idle")

        # 4. Di chuyển Út Sen tới Bàn T1 [9, 2]
        s.sim.pos = [9, 2]

        # 5. Bấm interact tại Bàn T1 -> Phục vụ món
        li.set(interact=True)
        events = s.step(li.advance())
        li.set(interact=False)
        self.assertIn("served", [e["name"] for e in events])
        snap = s.snapshot()
        self.assertIsNone(snap["hand"])  # Tay đã rảnh
        cust = next(c for c in snap["customers"] if c["id"] == "C1")
        self.assertEqual(cust["state"], "eating")

        # 6. Khách ăn trong 600 ticks (10 giây) -> Thanh toán + Tiền boa
        paid_event = None
        for _ in range(600):
            evs = s.step(li.advance())
            for e in evs:
                if e["name"] == "paid":
                    paid_event = e
        self.assertIsNotNone(paid_event)
        self.assertEqual(paid_event["data"]["money"], 60)
        self.assertEqual(paid_event["data"]["tip"], 12)  # 60 * 0.2 = 12

        snap = s.snapshot()
        self.assertEqual(len(snap["customers"]), 0)  # Khách đã rời bàn
        table = next(tb for tb in snap["tables"] if tb["id"] == "T1")
        self.assertIsNone(table["customer_id"])  # Bàn đã trống
        self.assertEqual(s.sim.money, 72)  # 60 + 12 = 72
        self.assertAlmostEqual(s.sim.reputation, 3.2, places=2)  # 3.0 + 0.2 = 3.2

    def test_quan_end_event(self):
        """Kiểm tra khi hết giờ ca tối thì phát quan_end với đúng tổng kết tài chính."""
        scenario = {
            "player": {"pos": [8, 5]},
            "time_left_ticks": 2,
        }
        s = Session("quan", self.tuning, scenario, seed=1)
        li = LiveInputs()
        s.step(li.advance())
        evs = s.step(li.advance())
        end_evs = [e for e in evs if e["name"] == "quan_end"]
        self.assertEqual(len(end_evs), 1)
        self.assertTrue(s.done)
        self.assertEqual(end_evs[0]["data"]["reason"], "time")


if __name__ == "__main__":
    unittest.main()
