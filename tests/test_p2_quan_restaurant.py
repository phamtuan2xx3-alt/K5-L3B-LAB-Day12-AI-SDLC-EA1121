"""Unit test độc lập cho Quán Ăn Chợ Nổi v1.1 (chonoi/sim/quan.py):
1. Khách đến theo lịch, xếp bàn T1, gọi món và giữ chỗ nguyên liệu.
2. Bếp nấu (cook_started, dish_ready), bưng bê (dish_picked), phục vụ (served).
3. Thanh toán tiền món và tiền boa (>= 50% kiên nhẫn), uy tín +0.2.
4. Hết kiên nhẫn bỏ về (customer_left), trừ uy tín -0.5.
5. Không đủ nguyên liệu phát no_dish.

Khi tích hợp với PR #2 (lát 3+4 theo Test Contract): đổi tên trường cho đúng PRD-0 D/E —
`dish` -> `dish_id`, `patience_ticks` -> `patience_ticks_left`, món trên tay là payload
{order_id, dish_id, base_price}, `paid` dùng `amount`. Kịch bản và luật kiểm giữ nguyên.
"""

import unittest

from chonoi.ids import IdAllocator
from chonoi.inputs import LiveInputs
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim


def make_inp(move=(0, 0), interact=False):
    inp = LiveInputs()
    inp.set(list(move), interact=interact)
    return inp.advance()


def make_tuning():
    return {
        "quan": {
            "duration_s": 180,
            "bounds": {"x": [0, 16], "z": [0, 10]},
            "start_pos": [8, 5],
            "walk_speed": 4.0,
            "ramp_max_ticks": 6,
            "interact_radius": 1.5,
            "stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [5, 8]}],
            "tables": [{"id": "T1", "pos": [9, 2]}, {"id": "T2", "pos": [13, 2]}],
            "first_customer_tick": 120,
            "customer_interval_s": 15,
            "patience_s": 60,
            "eat_s": 10,
            "tip_rate": 0.2,
            "tip_min_patience_ratio": 0.5,
            "tip_reputation": 0.2,
            "left_reputation_delta": -0.5,
            "reputation_initial": 3.0,
            "reputation_min": 0,
            "reputation_max": 5
        },
        "menu": {
            "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
            "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40}
        }
    }


class TestQuanRestaurant(unittest.TestCase):

    def test_customer_arrival_and_reserved_stock(self):
        """Khách đầu tiên đến ở tick 120, ngồi bàn T1, giữ chỗ nguyên liệu."""
        tuning = make_tuning()
        scenario = {"stock": {"ca_loc": 2, "bong_sung": 4}}
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        # Bước 119 ticks
        for _ in range(119):
            sim.step(make_inp())
        self.assertEqual(len(sim.customers), 0)

        # Tick 120: Khách đến
        evs = sim.step(make_inp())
        arr_evs = [e for e in evs if e[0] == "customer_arrived"]
        self.assertEqual(len(arr_evs), 1)
        self.assertEqual(len(sim.customers), 1)
        cust = sim.customers[0]
        self.assertEqual(cust["table_id"], "T1")
        self.assertIn(cust["dish_id"], ("ca_loc_nuong_trui", "goi_bong_sung"))

    def test_no_dish_when_stock_empty(self):
        """Kho rỗng: đến tick 120 phát no_dish và khách không ngồi bàn."""
        tuning = make_tuning()
        scenario = {"stock": {}}  # Không có nguyên liệu
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        for _ in range(119):
            sim.step(make_inp())
        evs = sim.step(make_inp())
        self.assertTrue(any(e[0] == "no_dish" for e in evs))
        self.assertEqual(len(sim.customers), 0)

    def test_kitchen_cooking_and_serving_cycle(self):
        """Quy trình hoàn chỉnh: nấu tại bếp B1 -> chín món -> bưng bê -> giao bàn T1 -> ăn -> trả tiền + tip."""
        tuning = make_tuning()
        # Đặt khách đang chờ tại T1 [9, 2] gọi món cá lóc nướng
        scenario = {
            "player": {"pos": [2.0, 8.0]},  # Ngay tại bếp B1 [2, 8]
            "stock": {"ca_loc": 1},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 3600}
            ]
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        # 1. Bấm interact tại bếp B1 -> Bắt đầu nấu
        evs = sim.step(make_inp(interact=True))
        self.assertTrue(any(e[0] == "cook_started" for e in evs))
        self.assertEqual(sim.stoves[0]["state"], "cooking")
        self.assertEqual(sim.stock.get("ca_loc", 0), 0)  # Đã trừ kho

        # 2. Chờ 6 giây (360 ticks) cho cá lóc chín
        for _ in range(359):
            sim.step(make_inp())
        evs_ready = sim.step(make_inp())
        self.assertTrue(any(e[0] == "dish_ready" for e in evs_ready))
        self.assertEqual(sim.stoves[0]["state"], "ready")

        # 3. Bấm interact tại bếp B1 -> Bưng món lên tay
        evs_pick = sim.step(make_inp(interact=True))
        self.assertTrue(any(e[0] == "dish_picked" for e in evs_pick))
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60})
        self.assertEqual(sim.stoves[0]["state"], "idle")

        # 4. Di chuyển tới bàn T1 [9, 2]
        sim.pos = [9.0, 2.0]
        evs_serve = sim.step(make_inp(interact=True))
        self.assertTrue(any(e[0] == "served" for e in evs_serve))
        self.assertIsNone(sim.hand)
        cust = sim.customers[0]
        self.assertEqual(cust["state"], "eating")
        self.assertEqual(cust["tip"], 12)  # 60 xu * 20% = 12 xu boa (vì còn >= 50% kiên nhẫn)

        # 5. Khách ăn 10s (600 ticks) -> Thanh toán
        for _ in range(599):
            sim.step(make_inp())
        evs_pay = sim.step(make_inp())
        pay_evs = [e for e in evs_pay if e[0] == "paid"]
        self.assertEqual(len(pay_evs), 1)
        self.assertEqual(pay_evs[0][1]["amount"], 72)  # 60 + 12 = 72
        self.assertEqual(sim.money, 72)
        # Uy tín tăng +0.2: 3.0 -> 3.2
        self.assertAlmostEqual(sim.reputation, 3.2, places=2)
        self.assertEqual(len(sim.customers), 0)

    def test_customer_left_when_patience_expires(self):
        """Khách chờ hết 60s kiên nhẫn mà không được phục vụ -> bỏ về, trừ 0.5 uy tín."""
        tuning = make_tuning()
        scenario = {
            "player": {"pos": [8.0, 5.0]},
            "stock": {"ca_loc": 1},
            "customers": [
                {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "state": "waiting", "patience_ticks_left": 2}
            ]
        }
        sim = QuanSim(tuning, scenario, Streams(1), IdAllocator())

        sim.step(make_inp())
        evs = sim.step(make_inp())
        left_evs = [e for e in evs if e[0] == "customer_left"]
        self.assertEqual(len(left_evs), 1)
        self.assertEqual(len(sim.customers), 0)
        # 3.0 - 0.5 = 2.5
        self.assertAlmostEqual(sim.reputation, 2.5, places=2)


if __name__ == "__main__":
    unittest.main()
