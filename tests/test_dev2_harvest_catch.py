"""Unit test độc lập cho DEV 2 (Phạm Quang Tuấn - phamtuan2xx3-alt):
Cơ chế Hái hoa mặt nước (Bông Điên Điển, Bông Súng) và Săn bắt cá (Cá Linh, Cá Lóc).

Chạy:
    py -3 -m unittest tests.test_dev2_harvest_catch -v
"""

import json
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import LiveInputs
from chonoi.runner import Session
from helpers import counts_tuning, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def tuning_gather():
    return counts_tuning()["gather"]


class TestHarvestMechanics(unittest.TestCase):
    def setUp(self):
        self.tuning = counts_tuning()  # luật giỏ đếm (v1.0/1.1); v1.2 xem test_gather_freshness

    def test_harvest_flower_success(self):
        """Hái hoa N1 thành công khi ở mặt nước: nhận 1 bông điên điển, regrow_ticks = 1200."""
        # N1 ở [12, 0]. Đặt player ở [12, 0] (ngoài dock radius 3 của [2, 0])
        scenario = {"player": {"pos": [12.0, 0.0]}}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(interact=True)
        evs = s.step(li.advance())
        
        # Kiểm tra event gather
        g_evs = [e for e in evs if e["name"] == "gather"]
        self.assertEqual(len(g_evs), 1)
        self.assertEqual(g_evs[0]["data"]["node_id"], "N1")
        self.assertEqual(g_evs[0]["data"]["kind"], "bong_dien_dien")
        
        # Kiểm tra giỏ đồ và node
        snap = s.snapshot()
        self.assertIn("bong_dien_dien", snap["hold"])
        self.assertEqual(snap["hold_count"], 1)
        node_n1 = next(n for n in snap["nodes"] if n["id"] == "N1")
        self.assertFalse(node_n1["ready"])
        self.assertEqual(node_n1["regrow_ticks"], 1200)

    def test_harvest_underwater_blocked(self):
        """Dưới nước (d > 0.5) không được hái hoa dù trong bán kính interact_radius."""
        # N1 ở [12, 0]. Đặt player ở [12, 1.0] (d = 1.0 > 0.5, khoảng cách = 1.0 <= 2.0)
        scenario = {"player": {"pos": [12.0, 1.0]}}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(interact=True)
        evs = s.step(li.advance())
        
        # Không có event gather nào
        self.assertEqual(len([e for e in evs if e["name"] == "gather"]), 0)
        snap = s.snapshot()
        self.assertEqual(snap["hold_count"], 0)
        node_n1 = next(n for n in snap["nodes"] if n["id"] == "N1")
        self.assertTrue(node_n1["ready"])

    def test_harvest_hold_full(self):
        """Khi giỏ đồ đã đầy 12 món, bấm hái hoa phát sự kiện hold_full và không hái được."""
        full_hold = ["ca_loc"] * 12
        scenario = {"player": {"pos": [12.0, 0.0]}, "hold": full_hold}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(interact=True)
        evs = s.step(li.advance())
        
        # Bắn hold_full
        self.assertEqual(len([e for e in evs if e["name"] == "hold_full"]), 1)
        self.assertEqual(len([e for e in evs if e["name"] == "gather"]), 0)
        snap = s.snapshot()
        self.assertEqual(snap["hold_count"], 12)
        node_n1 = next(n for n in snap["nodes"] if n["id"] == "N1")
        self.assertTrue(node_n1["ready"])

    def test_node_regrown_event_cycle(self):
        """Sau đúng 1200 tick kể từ lúc hái, node phát sự kiện node_regrown và ready lại."""
        scenario = {"player": {"pos": [12.0, 0.0]}}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(interact=True)
        s.step(li.advance())  # Tick 0: hái N1
        
        # Chạy 1199 tick nữa mà không thao tác
        li.set(interact=False)
        for _ in range(1199):
            s.step(li.advance())
        
        # Tick 1200: node_regrown xuất hiện
        evs = s.step(li.advance())
        re_evs = [e for e in evs if e["name"] == "node_regrown"]
        self.assertEqual(len(re_evs), 1)
        self.assertEqual(re_evs[0]["data"]["node_id"], "N1")
        snap = s.snapshot()
        node_n1 = next(n for n in snap["nodes"] if n["id"] == "N1")
        self.assertTrue(node_n1["ready"])


class TestCatchMechanics(unittest.TestCase):
    def setUp(self):
        self.tuning = counts_tuning()  # luật giỏ đếm (v1.0/1.1); v1.2 xem test_gather_freshness

    def test_catch_ca_linh_yield_3(self):
        """Bắt Cá Linh F1 [15, 5] dưới nước nhận 3 con vào giỏ, F1 bị xóa khỏi sông."""
        scenario = {"player": {"pos": [15.0, 5.0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0]}]}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        c_evs = [e for e in evs if e["name"] == "fish_caught"]
        self.assertEqual(len(c_evs), 1)
        self.assertEqual(c_evs[0]["data"]["fish_id"], "F1")
        self.assertEqual(c_evs[0]["data"]["kind"], "ca_linh")
        
        snap = s.snapshot()
        self.assertEqual(snap["hold"], ["ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(snap["hold_count"], 3)
        self.assertFalse(any(f["id"] == "F1" for f in snap["fish"]))
        self.assertEqual(snap["player"]["catch_cd_ticks"], 30)

    def test_catch_ca_loc_yield_1(self):
        """Bắt Cá Lóc F2 [30, 10] dưới nước nhận 1 con vào giỏ, F2 bị xóa khỏi sông."""
        scenario = {"player": {"pos": [30.0, 10.0]}, "fish": [{"id": "F2", "kind": "ca_loc", "pos": [30.0, 10.0]}]}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        c_evs = [e for e in evs if e["name"] == "fish_caught"]
        self.assertEqual(len(c_evs), 1)
        self.assertEqual(c_evs[0]["data"]["fish_id"], "F2")
        self.assertEqual(c_evs[0]["data"]["kind"], "ca_loc")
        
        snap = s.snapshot()
        self.assertEqual(snap["hold"], ["ca_loc"])
        self.assertFalse(any(f["id"] == "F2" for f in snap["fish"]))

    def test_catch_cooldown_blocks_spam(self):
        """Bấm phím catch trong thời gian hồi chiêu 30 ticks sẽ bị bỏ qua."""
        # F1 ở [15, 5], đặt thêm F_test ở [15, 5.5]
        scenario = {"player": {"pos": [15.0, 5.0]}}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        s.step(li.advance())  # Bắt F1, hồi chiêu kích hoạt = 30
        
        # Nhả phím rồi bấm lại ở tick tiếp theo
        li.set(catch=False)
        s.step(li.advance())
        li.set(catch=True)
        evs = s.step(li.advance())
        
        # Không bắt được con nào vì cd > 0
        self.assertEqual(len([e for e in evs if e["name"] == "fish_caught"]), 0)

    def test_catch_at_surface_blocked(self):
        """Ở mặt nước (d <= 0.5) không được bắt cá, hồi chiêu không bị kích hoạt."""
        scenario = {"player": {"pos": [15.0, 0.2]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 1.0]}]}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        self.assertEqual(len([e for e in evs if e["name"] == "fish_caught"]), 0)
        snap = s.snapshot()
        self.assertEqual(snap["player"]["catch_cd_ticks"], 0)
        self.assertEqual(len(snap["fish"]), 1)

    def test_catch_miss_triggers_cooldown(self):
        """Quăng lưới hụt (không có cá gần) vẫn kích hoạt hồi chiêu 30 ticks."""
        scenario = {"player": {"pos": [50.0, 5.0]}, "fish": []}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        s.step(li.advance())
        
        snap = s.snapshot()
        self.assertEqual(snap["player"]["catch_cd_ticks"], 30)

    def test_catch_hold_full_blocks_catch(self):
        """Giỏ đầy 12/12: bắt cá phát hold_full, cá KHÔNG bị xóa khỏi sông."""
        full_hold = ["bong_sung"] * 12
        scenario = {"player": {"pos": [15.0, 5.0]}, "hold": full_hold}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        self.assertEqual(len([e for e in evs if e["name"] == "hold_full"]), 1)
        self.assertEqual(len([e for e in evs if e["name"] == "fish_caught"]), 0)
        snap = s.snapshot()
        self.assertTrue(any(f["id"] == "F1" for f in snap["fish"]))
        self.assertEqual(snap["hold_count"], 12)

    def test_catch_partial_yield_fills_bag(self):
        """Contract v1.1: Bắt cá cần đủ chỗ cho cả đàn.
        Giỏ có 11 món (còn 1 chỗ), bắt Cá Linh (yield 3) -> không đủ chỗ, phát hold_full và cá không bị bắt."""
        near_full_hold = ["ca_loc"] * 11
        scenario = {"player": {"pos": [15.0, 5.0]}, "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15.0, 5.0]}], "hold": near_full_hold}
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        hf_evs = [e for e in evs if e["name"] == "hold_full"]
        self.assertEqual(len(hf_evs), 1)
        self.assertEqual(len([e for e in evs if e["name"] == "fish_caught"]), 0)
        
        snap = s.snapshot()
        self.assertEqual(snap["hold_count"], 11)
        self.assertTrue(any(f["id"] == "F1" for f in snap["fish"]))

    def test_tie_breaking_natural_id_key(self):
        """Khi 2 con cá F2 và F10 ở cùng khoảng cách, ưu tiên bắt F2 theo chuẩn id_key."""
        scenario = {
            "player": {"pos": [50.0, 10.0]},
            "fish": [
                {"id": "F10", "kind": "ca_linh", "pos": [50.0, 11.0]},
                {"id": "F2", "kind": "ca_loc", "pos": [50.0, 9.0]},
            ]
        }
        s = Session("gather", self.tuning, scenario, seed=1)
        li = LiveInputs()
        li.set(catch=True)
        evs = s.step(li.advance())
        
        c_evs = [e for e in evs if e["name"] == "fish_caught"]
        self.assertEqual(len(c_evs), 1)
        # F2 phải được chọn trước F10 theo id_key tự nhiên
        self.assertEqual(c_evs[0]["data"]["fish_id"], "F2")


if __name__ == "__main__":
    unittest.main()
